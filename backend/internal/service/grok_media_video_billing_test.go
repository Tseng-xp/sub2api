package service

import (
	"testing"
	"time"

	"github.com/stretchr/testify/require"
	"github.com/tidwall/gjson"
)

func TestGrokVideoE2EDurationFromCreatedAt(t *testing.T) {
	t.Parallel()
	created := time.Now().UTC().Add(-45 * time.Second)
	d := GrokVideoE2EDuration(created.Format(time.RFC3339Nano), time.Now().UTC())
	require.GreaterOrEqual(t, d, 44*time.Second)
	require.LessOrEqual(t, d, 47*time.Second)

	require.Equal(t, time.Duration(0), GrokVideoE2EDuration("", time.Now()))
	require.Equal(t, time.Duration(0), GrokVideoE2EDuration("not-a-time", time.Now()))
	// Future CreatedAt clamps to zero (clock skew).
	require.Equal(t, time.Duration(0), GrokVideoE2EDuration(time.Now().Add(time.Hour).UTC().Format(time.RFC3339Nano), time.Now()))
}

func TestGrokVideoPendingCreatedAtStampOnStoreShape(t *testing.T) {
	t.Parallel()
	// GrokVideoPendingCreatedAtNow must be parseable by GrokVideoE2EDuration.
	stamp := GrokVideoPendingCreatedAtNow()
	require.NotEmpty(t, stamp)
	d := GrokVideoE2EDuration(stamp, time.Now().UTC().Add(2*time.Second))
	require.GreaterOrEqual(t, d, time.Second)
	require.LessOrEqual(t, d, 3*time.Second)
}

func TestIsGrokVideoStatusBillable(t *testing.T) {
	t.Parallel()
	// Official success: status=done + video.url
	require.True(t, IsGrokVideoStatusBillable([]byte(`{
		"status":"done",
		"model":"grok-imagine-video-1.5",
		"video":{"url":"https://vidgen.x.ai/x.mp4","duration":8,"respect_moderation":true}
	}`)))

	// Official non-success states
	require.False(t, IsGrokVideoStatusBillable(nil))
	require.False(t, IsGrokVideoStatusBillable([]byte(`{"status":"pending"}`)))
	require.False(t, IsGrokVideoStatusBillable([]byte(`{"status":"expired"}`)))
	require.False(t, IsGrokVideoStatusBillable([]byte(`{"status":"failed"}`)))
	// done without video.url is not billable
	require.False(t, IsGrokVideoStatusBillable([]byte(`{"status":"done"}`)))
	// URL alone (legacy/non-official shapes) is not enough
	require.False(t, IsGrokVideoStatusBillable([]byte(`{"url":"https://example.com/v.mp4"}`)))
	require.False(t, IsGrokVideoStatusBillable([]byte(`{"download_url":"/v1/videos/task/content"}`)))
	// "completed" is not the official enum value
	require.False(t, IsGrokVideoStatusBillable([]byte(`{"status":"completed","video":{"url":"https://vidgen.x.ai/x.mp4"}}`)))

	// Configured v2 supplier success requires both completed and an output URL.
	require.True(t, IsGrokVideoStatusBillable([]byte(`{"task":{"status":"completed","outputs":["https://example.volces.com/video.mp4"]}}`)))
	require.False(t, IsGrokVideoStatusBillable([]byte(`{"task":{"status":"completed","outputs":[]}}`)))

	// Tencent TokenHub H3 success uses succeeded + task.content.url.
	require.True(t, IsGrokVideoStatusBillable([]byte(`{"task":{"status":"succeeded","content":{"url":"https://example.com/video.mp4"}}}`)))
	require.False(t, IsGrokVideoStatusBillable([]byte(`{"task":{"status":"running","content":{"url":"https://example.com/video.mp4"}}}`)))
	require.False(t, IsGrokVideoStatusBillable([]byte(`{"task":{"status":"succeeded"}}`)))
}

func TestParseGrokMediaRequestNativeVideoContent(t *testing.T) {
	t.Parallel()
	info := ParseGrokMediaRequest("application/json", []byte(`{
		"model":"public-video-model",
		"content":[
			{"type":"text","text":"city at night"},
			{"type":"image_url","image_url":{"url":"https://example.com/reference.png"},"role":"reference_image"}
		],
		"duration":10,
		"resolution":"1080p",
		"ratio":"16:9"
	}`))
	require.Equal(t, "city at night", info.Prompt)
	require.Equal(t, "16:9", info.AspectRatio)
	require.True(t, info.HasReferenceInput())
	require.Equal(t, []string{"https://example.com/reference.png"}, info.InputImageURLs)
}

func TestPrepareSeedanceV2VideoBodyConvertsLegacyRequest(t *testing.T) {
	t.Parallel()
	info := ParseGrokMediaRequest("application/json", []byte(`{
		"model":"public-video-model",
		"prompt":"city at night",
		"image":{"url":"https://example.com/reference.png"},
		"duration":10,
		"resolution":"1080p",
		"aspect_ratio":"16:9",
		"generate_audio":true
	}`))
	prepared, contentType, err := prepareSeedanceV2VideoBody(
		[]byte(`{"model":"public-video-model","prompt":"city at night","image":{"url":"https://example.com/reference.png"},"duration":10,"resolution":"1080p","aspect_ratio":"16:9","generate_audio":true}`),
		"application/json",
		info,
		"upstream-video-model",
	)
	require.NoError(t, err)
	require.Equal(t, "application/json", contentType)
	require.JSONEq(t, `{
		"model":"upstream-video-model",
		"content":[
			{"type":"text","text":"city at night"},
			{"type":"image_url","image_url":{"url":"https://example.com/reference.png"},"role":"reference_image"}
		],
		"duration":10,
		"resolution":"1080p",
		"ratio":"16:9",
		"generate_audio":true
	}`, string(prepared))
}

func TestPrepareTencentTokenHubVideoBodyConvertsLegacyRequest(t *testing.T) {
	info := ParseGrokMediaRequest("application/json", []byte(`{
		"model":"hailuo-h3",
		"prompt":"ocean at sunrise",
		"image":{"url":"https://example.com/first.png"},
		"duration":6,
		"resolution":"1080p",
		"aigc_watermark":true
	}`))
	prepared, contentType, normalized, err := prepareTencentTokenHubVideoBody(
		[]byte(`{"model":"hailuo-h3","prompt":"ocean at sunrise","image":{"url":"https://example.com/first.png"},"duration":6,"resolution":"1080p","aigc_watermark":true}`),
		"application/json",
		info,
		"minimax-video-h3",
	)
	require.NoError(t, err)
	require.Equal(t, "application/json", contentType)
	require.Equal(t, VideoBillingResolution768P, normalized.Resolution)
	require.JSONEq(t, `{
		"model":"minimax-video-h3",
		"content":[
			{"type":"text","text":"ocean at sunrise"},
			{"type":"image_url","image_url":{"url":"https://example.com/first.png"},"role":"first_frame"}
		],
		"duration":6,
		"resolution":"768P",
		"aigc_watermark":true
	}`, string(prepared))
}

func TestPrepareTencentTokenHubVideoBodyDefaultsTextRatioAndSupports2K(t *testing.T) {
	info := ParseGrokMediaRequest("application/json", []byte(`{
		"model":"hailuo-h3","prompt":"city flyover","duration":8,"resolution":"2K"
	}`))
	prepared, _, normalized, err := prepareTencentTokenHubVideoBody(
		[]byte(`{"model":"hailuo-h3","prompt":"city flyover","duration":8,"resolution":"2K"}`),
		"application/json",
		info,
		"minimax-video-h3",
	)
	require.NoError(t, err)
	require.Equal(t, VideoBillingResolution2K, normalized.Resolution)
	require.Equal(t, "2K", gjson.GetBytes(prepared, "resolution").String())
	require.Equal(t, "16:9", gjson.GetBytes(prepared, "ratio").String())
}

func TestExtractGrokVideoBillingFromStatusBodyPrefersUpstreamParams(t *testing.T) {
	t.Parallel()
	pending := &GrokVideoPendingBilling{
		Model:                "pending-model",
		BillingModel:         "pending-billing",
		UpstreamModel:        "pending-upstream",
		VideoResolution:      VideoBillingResolution720P,
		VideoDurationSeconds: 8,
	}
	// Official completed body from docs.x.ai Video Generation.
	body := []byte(`{
		"status":"done",
		"model":"grok-imagine-video-1.5",
		"video":{"url":"https://vidgen.x.ai/signed.mp4","duration":12,"respect_moderation":true}
	}`)
	result := ExtractGrokVideoBillingFromStatusBody(body, pending, "req-1")
	require.NotNil(t, result)
	require.Equal(t, 1, result.VideoCount)
	require.Equal(t, "grok-imagine-video-1.5", result.Model)
	// Resolution is not in official status response — use create-time request.
	require.Equal(t, VideoBillingResolution720P, result.VideoResolution)
	// Duration prefers official video.duration.
	require.Equal(t, 12, result.VideoDurationSeconds)
}

func TestExtractGrokVideoBillingFromStatusBodyFallsBackToPending(t *testing.T) {
	t.Parallel()
	pending := &GrokVideoPendingBilling{
		Model:                "create-model",
		BillingModel:         "create-billing",
		UpstreamModel:        "create-upstream",
		VideoResolution:      VideoBillingResolution1080P,
		VideoDurationSeconds: 10,
	}
	// done + video.url, but no model/duration in body.
	body := []byte(`{"status":"done","video":{"url":"https://vidgen.x.ai/signed.mp4"}}`)
	result := ExtractGrokVideoBillingFromStatusBody(body, pending, "req-2")
	require.NotNil(t, result)
	require.Equal(t, "create-billing", result.BillingModel)
	require.Equal(t, "create-upstream", result.UpstreamModel)
	require.Equal(t, VideoBillingResolution1080P, result.VideoResolution)
	require.Equal(t, 10, result.VideoDurationSeconds)
}

func TestExtractGrokVideoBillingFromSeedanceV2StatusUsesUsage(t *testing.T) {
	t.Parallel()
	pending := &GrokVideoPendingBilling{
		Model:                  "public-video-model",
		BillingModel:           "public-video-model",
		UpstreamModel:          "upstream-video-model",
		VideoResolution:        VideoBillingResolution1080P,
		VideoDurationSeconds:   10,
		VideoHasReferenceInput: true,
	}
	body := []byte(`{
		"task":{
			"id":"task-123",
			"status":"completed",
			"model":"upstream-video-model",
			"duration_seconds":10,
			"outputs":["https://example.volces.com/video.mp4"],
			"usage":{"completion_tokens":250000,"total_tokens":250000},
			"metadata":{"resolution":"1080p"}
		}
	}`)
	result := ExtractGrokVideoBillingFromStatusBody(body, pending, "task-123")
	require.NotNil(t, result)
	require.Equal(t, "task-123", result.ResponseID)
	require.Equal(t, "public-video-model", result.BillingModel)
	require.Equal(t, "upstream-video-model", result.UpstreamModel)
	require.Equal(t, 250000, result.Usage.OutputTokens)
	require.True(t, result.VideoHasReferenceInput)
	require.Equal(t, VideoBillingResolution1080P, result.VideoResolution)
}

func TestExtractGrokVideoBillingFromTencentTokenHubStatusUsesAuthoritativeTotal(t *testing.T) {
	pending := &GrokVideoPendingBilling{
		Model:                  "hailuo-h3",
		BillingModel:           "hailuo-h3",
		UpstreamModel:          "minimax-video-h3",
		VideoResolution:        VideoBillingResolution2K,
		VideoDurationSeconds:   6,
		VideoHasReferenceInput: true,
	}
	body := []byte(`{
		"request_id":"request-1",
		"task":{
			"id":"task-h3",
			"status":"succeeded",
			"content":{"url":"https://example.com/h3.mp4"},
			"usage":{"input_seconds":2,"output_seconds":6,"input_image_count":1}
		},
		"tokenhub_usage":{"total_tokens":640000}
	}`)
	result := ExtractGrokVideoBillingFromStatusBody(body, pending, "task-h3")
	require.NotNil(t, result)
	require.Equal(t, "request-1", result.ResponseID)
	require.Equal(t, 640000, result.Usage.OutputTokens)
	require.Equal(t, 6, result.VideoDurationSeconds)
	require.Equal(t, VideoBillingResolution2K, result.VideoResolution)
	require.True(t, result.VideoHasReferenceInput)
}

func TestExtractGrokVideoBillingRejectsNonDoneStatus(t *testing.T) {
	t.Parallel()
	pending := &GrokVideoPendingBilling{Model: "m", VideoDurationSeconds: 8, VideoResolution: "720p"}
	require.Nil(t, ExtractGrokVideoBillingFromStatusBody(
		[]byte(`{"status":"pending","video":{"url":"https://vidgen.x.ai/x.mp4","duration":8}}`),
		pending, "req",
	))
	require.Nil(t, ExtractGrokVideoBillingFromStatusBody(
		[]byte(`{"status":"completed","video":{"url":"https://vidgen.x.ai/x.mp4","duration":8}}`),
		pending, "req",
	))
}

func TestGrokMediaUsageFromResponseVideoCreateDoesNotBill(t *testing.T) {
	t.Parallel()
	info := GrokMediaRequestInfo{Model: "grok-imagine-video", Resolution: "720p", DurationSeconds: 10}
	meta := grokMediaUsageFromResponse(GrokMediaEndpointVideosGenerations, info, []byte(`{"request_id":"v1"}`))
	require.Equal(t, "v1", meta.ResponseID)
	require.Equal(t, 0, meta.VideoCount)
	require.Equal(t, 10, meta.VideoDurationSeconds)
	require.Equal(t, VideoBillingResolution720P, meta.VideoResolution)
}

func TestGrokMediaUsageFromResponseVideoCreateCapturesReferenceInput(t *testing.T) {
	t.Parallel()
	info := GrokMediaRequestInfo{
		Model:           "custom-video-model",
		Resolution:      "1080p",
		DurationSeconds: 5,
		InputImageURLs:  []string{"https://example.com/reference.png"},
	}
	meta := grokMediaUsageFromResponse(GrokMediaEndpointVideosGenerations, info, []byte(`{"request_id":"seedance-1"}`))
	require.True(t, meta.VideoHasReferenceInput)
}

func TestGrokMediaUsageFromResponseVideoStatusBillsOnOfficialDone(t *testing.T) {
	t.Parallel()
	meta := grokMediaUsageFromResponse(
		GrokMediaEndpointVideoStatus,
		GrokMediaRequestInfo{},
		[]byte(`{"status":"done","model":"grok-imagine-video-1.5","video":{"url":"https://vidgen.x.ai/a.mp4","duration":9}}`),
	)
	require.Equal(t, 1, meta.VideoCount)
	require.Equal(t, 9, meta.VideoDurationSeconds)
	require.Equal(t, "grok-imagine-video-1.5", meta.Model)

	// Official non-done must not set billable units.
	pendingOnly := grokMediaUsageFromResponse(
		GrokMediaEndpointVideoStatus,
		GrokMediaRequestInfo{},
		[]byte(`{"status":"pending"}`),
	)
	require.Equal(t, 0, pendingOnly.VideoCount)

	// completed is not official done.
	completed := grokMediaUsageFromResponse(
		GrokMediaEndpointVideoStatus,
		GrokMediaRequestInfo{},
		[]byte(`{"status":"completed","video":{"url":"https://vidgen.x.ai/a.mp4","duration":9}}`),
	)
	require.Equal(t, 0, completed.VideoCount)
}
