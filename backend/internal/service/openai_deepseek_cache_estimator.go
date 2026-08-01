package service

import (
	"fmt"
	"strings"
	"sync"
	"time"

	"github.com/Wei-Shaw/sub2api/internal/pkg/logger"
	"go.uber.org/zap"
)

const (
	deepSeekCacheUsageEstimationExtraKey = "deepseek_cache_usage_estimation_enabled"
	deepSeekCacheUsageEstimationTTL      = 5 * time.Minute
	deepSeekCacheBlockTokens             = 64
	deepSeekCacheEstimateMaxEntries      = 65536
)

type deepSeekCacheEstimateEntry struct {
	inputTokens   int
	contextTokens int
	expiresAt     time.Time
}

type deepSeekCacheEstimator struct {
	mu      sync.Mutex
	entries map[string]deepSeekCacheEstimateEntry
}

func newDeepSeekCacheEstimator() *deepSeekCacheEstimator {
	return &deepSeekCacheEstimator{entries: make(map[string]deepSeekCacheEstimateEntry, 256)}
}

func (e *deepSeekCacheEstimator) previousAndRemember(key string, inputTokens, outputTokens int, now time.Time) (deepSeekCacheEstimateEntry, bool) {
	if e == nil || key == "" || inputTokens <= 0 {
		return deepSeekCacheEstimateEntry{}, false
	}

	e.mu.Lock()
	defer e.mu.Unlock()

	previous, ok := e.entries[key]
	if ok && !now.Before(previous.expiresAt) {
		ok = false
		delete(e.entries, key)
	}

	if len(e.entries) >= deepSeekCacheEstimateMaxEntries {
		for entryKey, entry := range e.entries {
			if !now.Before(entry.expiresAt) {
				delete(e.entries, entryKey)
			}
		}
	}
	if len(e.entries) >= deepSeekCacheEstimateMaxEntries {
		for entryKey := range e.entries {
			delete(e.entries, entryKey)
			break
		}
	}

	e.entries[key] = deepSeekCacheEstimateEntry{
		inputTokens:   inputTokens,
		contextTokens: inputTokens + max(outputTokens, 0),
		expiresAt:     now.Add(deepSeekCacheUsageEstimationTTL),
	}
	return previous, ok
}

func (s *OpenAIGatewayService) getDeepSeekCacheEstimator() *deepSeekCacheEstimator {
	if s == nil {
		return nil
	}
	s.deepSeekCacheEstimatorOnce.Do(func() {
		s.deepSeekCacheEstimator = newDeepSeekCacheEstimator()
	})
	return s.deepSeekCacheEstimator
}

// ApplyMissingDeepSeekCacheUsageEstimate fills billing-only cache usage for an
// explicitly opted-in compatible upstream that reports total input usage but
// always omits (or zeroes) per-request cache hits. The estimate is conservative:
// the first turn remains a miss, shorter contexts are never converted, and a
// later turn can reuse at most the preceding confirmed context in 64-token
// blocks. A real positive upstream cache value always wins.
func (s *OpenAIGatewayService) ApplyMissingDeepSeekCacheUsageEstimate(result *OpenAIForwardResult, apiKey *APIKey, account *Account, sessionHash string) {
	if result == nil || apiKey == nil || account == nil || result.Usage.InputTokens <= 0 {
		return
	}
	if account.Platform != PlatformOpenAI || account.Type != AccountTypeAPIKey || !account.getExtraBool(deepSeekCacheUsageEstimationExtraKey) {
		return
	}
	if !isDeepSeekV4FlashUsageModel(result) || strings.TrimSpace(sessionHash) == "" {
		return
	}

	key := fmt.Sprintf("%d:%d:%s:%s", apiKey.ID, account.ID, strings.ToLower(strings.TrimSpace(result.Model)), sessionHash)
	previous, ok := s.getDeepSeekCacheEstimator().previousAndRemember(
		key,
		result.Usage.InputTokens,
		result.Usage.OutputTokens,
		time.Now(),
	)
	if result.Usage.CacheReadInputTokens > 0 || !ok || result.Usage.InputTokens < previous.inputTokens {
		return
	}

	estimated := min(previous.contextTokens, result.Usage.InputTokens)
	estimated -= estimated % deepSeekCacheBlockTokens
	if estimated <= 0 {
		return
	}
	result.Usage.CacheReadInputTokens = estimated
	logger.L().Info("openai_usage.deepseek_cache_locally_estimated",
		zap.Int64("account_id", account.ID),
		zap.Int64("api_key_id", apiKey.ID),
		zap.String("model", result.Model),
		zap.String("session_hash", shortSessionHash(sessionHash)),
		zap.Int("input_tokens", result.Usage.InputTokens),
		zap.Int("estimated_cache_read_tokens", estimated),
	)
}

func isDeepSeekV4FlashUsageModel(result *OpenAIForwardResult) bool {
	if result == nil {
		return false
	}
	for _, model := range []string{result.Model, result.BillingModel, result.UpstreamModel} {
		if strings.EqualFold(strings.TrimSpace(model), "deepseek-v4-flash") {
			return true
		}
	}
	return false
}
