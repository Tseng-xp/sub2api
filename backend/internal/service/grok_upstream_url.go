package service

import (
	"context"
	"errors"
	"fmt"
	"net/url"
	"strings"

	"github.com/Wei-Shaw/sub2api/internal/config"
	"github.com/Wei-Shaw/sub2api/internal/pkg/xai"
	"github.com/Wei-Shaw/sub2api/internal/util/urlvalidator"
)

const seedanceV2MediaHost = "model.service-inference.ai"

var tencentTokenHubMediaHosts = map[string]struct{}{
	"tokenhub.tencentmaas.com":           {},
	"tokenhub-intl.tencentcloudmaas.com": {},
}

// isSeedanceV2MediaBaseURL selects the supplier-specific video adapter by the
// operator-configured account endpoint. Pricing and model aliases stay in the
// database; this only chooses the upstream wire protocol.
func isSeedanceV2MediaBaseURL(raw string) bool {
	parsed, err := url.Parse(strings.TrimSpace(raw))
	return err == nil && strings.EqualFold(parsed.Hostname(), seedanceV2MediaHost)
}

// isTencentTokenHubMediaBaseURL selects Tencent TokenHub's MiniMax H3/H3-Max
// adapter. TokenHub uses Bearer authentication like Grok API-key accounts, but
// its asynchronous video endpoints and terminal response shape are different.
func isTencentTokenHubMediaBaseURL(raw string) bool {
	parsed, err := url.Parse(strings.TrimSpace(raw))
	if err != nil {
		return false
	}
	_, ok := tencentTokenHubMediaHosts[strings.ToLower(parsed.Hostname())]
	return ok
}

func buildTencentTokenHubMediaURL(baseURL string, endpoint GrokMediaEndpoint, requestID string, validator xai.BaseURLValidator) (string, error) {
	validated, err := validator(baseURL)
	if err != nil {
		return "", fmt.Errorf("invalid base url: %w", err)
	}
	parsed, err := url.Parse(validated)
	if err != nil {
		return "", fmt.Errorf("invalid base url: %w", err)
	}
	// The account URL may be saved as the host, /v1, or the complete create
	// endpoint. Always rebuild the documented V2 endpoint from the origin.
	parsed.Path = ""
	parsed.RawPath = ""
	switch endpoint {
	case GrokMediaEndpointVideosGenerations:
		parsed.Path = "/v1/wand/minimax-video-v2/generation"
	case GrokMediaEndpointVideoStatus:
		requestID = strings.TrimSpace(requestID)
		if requestID == "" {
			return "", fmt.Errorf("tencent tokenhub video task id is required")
		}
		parsed.Path = "/v1/wand/minimax-video-v2/tasks/" + url.PathEscape(requestID)
	case GrokMediaEndpointVideoContent:
		return "", fmt.Errorf("tencent tokenhub video content is available only from the signed task output URL")
	default:
		return "", fmt.Errorf("unsupported tencent tokenhub media endpoint: %s", endpoint)
	}
	parsed.RawQuery = ""
	parsed.Fragment = ""
	return parsed.String(), nil
}

func buildSeedanceV2MediaURL(baseURL string, endpoint GrokMediaEndpoint, requestID string, validator xai.BaseURLValidator) (string, error) {
	validated, err := validator(baseURL)
	if err != nil {
		return "", fmt.Errorf("invalid base url: %w", err)
	}
	parsed, err := url.Parse(validated)
	if err != nil {
		return "", fmt.Errorf("invalid base url: %w", err)
	}
	prefix := strings.TrimRight(parsed.EscapedPath(), "/")
	for _, suffix := range []string{"/v1", "/v2"} {
		if strings.HasSuffix(strings.ToLower(prefix), suffix) {
			prefix = prefix[:len(prefix)-len(suffix)]
			break
		}
	}
	switch endpoint {
	case GrokMediaEndpointVideosGenerations:
		parsed.Path = prefix + "/v2/video/generate"
		parsed.RawPath = ""
	case GrokMediaEndpointVideoStatus:
		requestID = strings.TrimSpace(requestID)
		if requestID == "" {
			return "", fmt.Errorf("seedance video task id is required")
		}
		parsed.Path = prefix + "/v2/video/tasks/" + url.PathEscape(requestID)
		parsed.RawPath = ""
	case GrokMediaEndpointVideoContent:
		return "", fmt.Errorf("seedance video content is available only from the signed task output URL")
	default:
		return "", fmt.Errorf("unsupported seedance v2 media endpoint: %s", endpoint)
	}
	parsed.RawQuery = ""
	parsed.Fragment = ""
	return parsed.String(), nil
}

func grokBaseURLValidator(account *Account, cfg *config.Config) (xai.BaseURLValidator, error) {
	if account == nil || !account.IsGrok() {
		return nil, fmt.Errorf("grok account is required")
	}
	switch account.Type {
	case AccountTypeOAuth:
		// Official gateway hosts are always trusted and always usable, even when
		// the operator enables a restrictive URL allowlist. A custom forwarding
		// host is vetted by the same operator policy as API-key accounts.
		//
		// The official-vs-custom decision is made on the host, not via
		// ValidateTrustedBaseURL: that validator relaxes to accept-any under the
		// XAI_ALLOW_UNSAFE_URL_OVERRIDES debug switch, which must never let an
		// OAuth bearer token reach an arbitrary custom host.
		policyValidator := grokOperatorPolicyValidator(cfg)
		return redactedGrokBaseURLValidator(func(raw string) (string, error) {
			if xai.IsOfficialBaseURL(raw) {
				return xai.ValidateTrustedBaseURL(raw)
			}
			return policyValidator(raw)
		}), nil
	case AccountTypeAPIKey:
		return redactedGrokBaseURLValidator(grokOperatorPolicyValidator(cfg)), nil
	default:
		return nil, fmt.Errorf("unsupported grok account type: %s", account.Type)
	}
}

// grokOperatorPolicyValidator 按全局出站 URL 安全策略校验自定义 base_url：
// 白名单开启时强制 UpstreamHosts；关闭时仅做格式校验（HTTP 允许与否跟随配置）。
func grokOperatorPolicyValidator(cfg *config.Config) xai.BaseURLValidator {
	if cfg == nil {
		return xai.ValidateBaseURL
	}
	if !cfg.Security.URLAllowlist.Enabled {
		return func(raw string) (string, error) {
			return urlvalidator.ValidateURLFormat(raw, cfg.Security.URLAllowlist.AllowInsecureHTTP)
		}
	}
	return func(raw string) (string, error) {
		return urlvalidator.ValidateHTTPSURL(raw, urlvalidator.ValidationOptions{
			AllowedHosts:     cfg.Security.URLAllowlist.UpstreamHosts,
			RequireAllowlist: true,
			AllowPrivate:     cfg.Security.URLAllowlist.AllowPrivateHosts,
		})
	}
}

func redactedGrokBaseURLValidator(validator xai.BaseURLValidator) xai.BaseURLValidator {
	return func(raw string) (string, error) {
		validated, err := validator(raw)
		if err != nil {
			return "", errors.New("base URL rejected by URL security policy")
		}
		return validated, nil
	}
}

func buildGrokResponsesURL(account *Account, cfg *config.Config, settings ...*SettingService) (string, error) {
	validator, err := grokBaseURLValidator(account, cfg)
	if err != nil {
		return "", err
	}
	baseURL := account.GetGrokBaseURL()
	if len(settings) > 0 && settings[0] != nil {
		baseURL = settings[0].ResolveGrokBaseURL(context.Background(), account)
	}
	return xai.BuildResponsesURLWithValidator(baseURL, validator)
}

func buildGrokChatCompletionsURL(account *Account, cfg *config.Config, settings ...*SettingService) (string, error) {
	validator, err := grokBaseURLValidator(account, cfg)
	if err != nil {
		return "", err
	}
	baseURL := account.GetGrokBaseURL()
	if len(settings) > 0 && settings[0] != nil {
		baseURL = settings[0].ResolveGrokBaseURL(context.Background(), account)
	}
	return xai.BuildChatCompletionsURLWithValidator(baseURL, validator)
}

// buildGrokBillingURL 解析 billing 探测端点：跟随账号的转发 base_url，
// 未定制的账号仍指向官方 CLI 网关。
func buildGrokBillingURL(account *Account, cfg *config.Config, weekly bool) (string, error) {
	validator, err := grokBaseURLValidator(account, cfg)
	if err != nil {
		return "", err
	}
	baseURL := account.GetGrokBaseURL()
	// Official public/regional API hosts do not expose Grok Build billing.
	// Keep custom relays on their configured host because they may proxy the CLI
	// billing path alongside inference.
	if xai.IsOfficialBaseURL(baseURL) && !isGrokCLIProxyBaseURL(baseURL) {
		baseURL = xai.DefaultCLIBaseURL
	}
	return xai.BuildBillingURLWithValidator(baseURL, weekly, validator)
}

func buildGrokMediaURL(account *Account, cfg *config.Config, endpoint GrokMediaEndpoint, requestID string) (string, error) {
	validator, err := grokBaseURLValidator(account, cfg)
	if err != nil {
		return "", err
	}
	baseURL := account.GetGrokMediaBaseURL()
	if isSeedanceV2MediaBaseURL(baseURL) {
		return buildSeedanceV2MediaURL(baseURL, endpoint, requestID, validator)
	}
	if isTencentTokenHubMediaBaseURL(baseURL) {
		return buildTencentTokenHubMediaURL(baseURL, endpoint, requestID, validator)
	}
	switch endpoint {
	case GrokMediaEndpointImagesGenerations:
		return xai.BuildImagesGenerationsURLWithValidator(baseURL, validator)
	case GrokMediaEndpointImagesEdits:
		return xai.BuildImagesEditsURLWithValidator(baseURL, validator)
	case GrokMediaEndpointVideosGenerations:
		return xai.BuildVideosGenerationsURLWithValidator(baseURL, validator)
	case GrokMediaEndpointVideosEdits:
		return xai.BuildVideosEditsURLWithValidator(baseURL, validator)
	case GrokMediaEndpointVideosExtensions:
		return xai.BuildVideosExtensionsURLWithValidator(baseURL, validator)
	case GrokMediaEndpointVideoStatus:
		return xai.BuildVideoURLWithValidator(baseURL, requestID, validator)
	case GrokMediaEndpointVideoContent:
		videoURL, err := xai.BuildVideoURLWithValidator(baseURL, requestID, validator)
		if err != nil {
			return "", err
		}
		return videoURL + "/content", nil
	default:
		return "", fmt.Errorf("unsupported grok media endpoint: %s", endpoint)
	}
}

// buildGrokVoiceURL returns the official xAI Voice API endpoint.
// Voice HTTP (/tts, /stt, /custom-voices) and WS (/realtime) are only exposed
// by api.x.ai — the CLI chat proxy does not implement them. When the account
// base_url points at the CLI proxy (or is empty), fall back to DefaultBaseURL.
func buildGrokVoiceURL(account *Account, cfg *config.Config, endpoint string) (string, error) {
	validator, err := grokBaseURLValidator(account, cfg)
	if err != nil {
		return "", err
	}
	base := ""
	if account != nil {
		base = account.GetGrokMediaBaseURL()
	}
	if strings.TrimSpace(base) == "" || isGrokCLIProxyBaseURL(base) {
		base = xai.DefaultBaseURL
	}
	validated, err := validator(base)
	if err != nil {
		return "", err
	}
	ep := strings.Trim(strings.TrimSpace(endpoint), "/")
	if ep == "" {
		return "", fmt.Errorf("voice endpoint is required")
	}
	parts := strings.Split(ep, "/")
	encoded := make([]string, 0, len(parts))
	for _, part := range parts {
		if strings.TrimSpace(part) == "" || part == "." || part == ".." {
			return "", fmt.Errorf("invalid voice endpoint path")
		}
		encoded = append(encoded, url.PathEscape(part))
	}
	return strings.TrimRight(validated, "/") + "/" + strings.Join(encoded, "/"), nil
}

func isGrokCLIProxyBaseURL(raw string) bool {
	return isGrokCLIProxyTarget(raw)
}
