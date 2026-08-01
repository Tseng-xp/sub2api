package service

import (
	"testing"
	"time"

	"github.com/stretchr/testify/require"
)

func TestDeepSeekCacheEstimatorPreviousAndRemember(t *testing.T) {
	estimator := newDeepSeekCacheEstimator()
	now := time.Now()

	_, ok := estimator.previousAndRemember("session", 1000, 10, now)
	require.False(t, ok, "first turn must remain an uncached miss")

	previous, ok := estimator.previousAndRemember("session", 1200, 20, now.Add(time.Second))
	require.True(t, ok)
	require.Equal(t, 1000, previous.inputTokens)
	require.Equal(t, 1010, previous.contextTokens)

	_, ok = estimator.previousAndRemember("session", 1300, 20, now.Add(deepSeekCacheUsageEstimationTTL+time.Second))
	require.False(t, ok, "expired observations must not be treated as cache hits")
}

func TestApplyMissingDeepSeekCacheUsageEstimate(t *testing.T) {
	account := &Account{
		ID:       6,
		Platform: PlatformOpenAI,
		Type:     AccountTypeAPIKey,
		Extra: map[string]any{
			deepSeekCacheUsageEstimationExtraKey: true,
		},
	}
	apiKey := &APIKey{ID: 12}
	service := &OpenAIGatewayService{}

	first := &OpenAIForwardResult{
		Model: "deepseek-v4-flash",
		Usage: OpenAIUsage{InputTokens: 1000, OutputTokens: 10},
	}
	service.ApplyMissingDeepSeekCacheUsageEstimate(first, apiKey, account, "session-a")
	require.Zero(t, first.Usage.CacheReadInputTokens)

	second := &OpenAIForwardResult{
		Model: "deepseek-v4-flash",
		Usage: OpenAIUsage{InputTokens: 1200, OutputTokens: 20},
	}
	service.ApplyMissingDeepSeekCacheUsageEstimate(second, apiKey, account, "session-a")
	require.Equal(t, 960, second.Usage.CacheReadInputTokens)

	upstreamReported := &OpenAIForwardResult{
		Model: "deepseek-v4-flash",
		Usage: OpenAIUsage{InputTokens: 1400, OutputTokens: 20, CacheReadInputTokens: 512},
	}
	service.ApplyMissingDeepSeekCacheUsageEstimate(upstreamReported, apiKey, account, "session-a")
	require.Equal(t, 512, upstreamReported.Usage.CacheReadInputTokens, "positive upstream usage must win")
}

func TestApplyMissingDeepSeekCacheUsageEstimateScope(t *testing.T) {
	baseResult := func() *OpenAIForwardResult {
		return &OpenAIForwardResult{
			Model: "deepseek-v4-flash",
			Usage: OpenAIUsage{InputTokens: 1000, OutputTokens: 10},
		}
	}
	apiKey := &APIKey{ID: 12}

	t.Run("account must opt in", func(t *testing.T) {
		service := &OpenAIGatewayService{}
		account := &Account{ID: 6, Platform: PlatformOpenAI, Type: AccountTypeAPIKey}
		service.ApplyMissingDeepSeekCacheUsageEstimate(baseResult(), apiKey, account, "session")
		second := baseResult()
		service.ApplyMissingDeepSeekCacheUsageEstimate(second, apiKey, account, "session")
		require.Zero(t, second.Usage.CacheReadInputTokens)
	})

	t.Run("other models are unchanged", func(t *testing.T) {
		service := &OpenAIGatewayService{}
		account := &Account{
			ID:       6,
			Platform: PlatformOpenAI,
			Type:     AccountTypeAPIKey,
			Extra: map[string]any{
				deepSeekCacheUsageEstimationExtraKey: true,
			},
		}
		first := baseResult()
		first.Model = "deepseek-v4-pro"
		service.ApplyMissingDeepSeekCacheUsageEstimate(first, apiKey, account, "session")
		second := baseResult()
		second.Model = "deepseek-v4-pro"
		service.ApplyMissingDeepSeekCacheUsageEstimate(second, apiKey, account, "session")
		require.Zero(t, second.Usage.CacheReadInputTokens)
	})

	t.Run("shorter contexts remain misses", func(t *testing.T) {
		service := &OpenAIGatewayService{}
		account := &Account{
			ID:       6,
			Platform: PlatformOpenAI,
			Type:     AccountTypeAPIKey,
			Extra: map[string]any{
				deepSeekCacheUsageEstimationExtraKey: true,
			},
		}
		service.ApplyMissingDeepSeekCacheUsageEstimate(baseResult(), apiKey, account, "session")
		shorter := baseResult()
		shorter.Usage.InputTokens = 900
		service.ApplyMissingDeepSeekCacheUsageEstimate(shorter, apiKey, account, "session")
		require.Zero(t, shorter.Usage.CacheReadInputTokens)
	})
}
