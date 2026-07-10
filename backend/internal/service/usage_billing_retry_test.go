package service

import (
	"context"
	"errors"
	"testing"

	"github.com/stretchr/testify/require"
)

// scriptedUsageBillingRepo 按脚本依次返回错误，用于测试计费重试。
// errs[i] 为第 i 次 Apply 的返回错误；nil 表示成功。
type scriptedUsageBillingRepo struct {
	UsageBillingRepository
	errs  []error
	calls int
}

func (s *scriptedUsageBillingRepo) Apply(_ context.Context, _ *UsageBillingCommand) (*UsageBillingApplyResult, error) {
	i := s.calls
	s.calls++
	if i < len(s.errs) && s.errs[i] != nil {
		return nil, s.errs[i]
	}
	return &UsageBillingApplyResult{Applied: true}, nil
}

// 瞬时错误应重试并在后续尝试成功；Apply 幂等，重试不重复扣费。
func TestApplyUsageBillingWithRetry_TransientThenSuccess(t *testing.T) {
	repo := &scriptedUsageBillingRepo{errs: []error{errors.New("connection reset"), nil}}
	res, err := applyUsageBillingWithRetry(context.Background(), repo, &UsageBillingCommand{RequestID: "r1", APIKeyID: 1})
	require.NoError(t, err)
	require.NotNil(t, res)
	require.True(t, res.Applied)
	require.Equal(t, 2, repo.calls)
}

// 终态业务错误（去重指纹冲突）不重试。
func TestApplyUsageBillingWithRetry_TerminalNotRetried(t *testing.T) {
	repo := &scriptedUsageBillingRepo{errs: []error{ErrUsageBillingRequestConflict}}
	_, err := applyUsageBillingWithRetry(context.Background(), repo, &UsageBillingCommand{RequestID: "r1", APIKeyID: 1})
	require.ErrorIs(t, err, ErrUsageBillingRequestConflict)
	require.Equal(t, 1, repo.calls)
}

// context 取消/超时不重试。
func TestApplyUsageBillingWithRetry_ContextErrNotRetried(t *testing.T) {
	repo := &scriptedUsageBillingRepo{errs: []error{context.DeadlineExceeded}}
	_, err := applyUsageBillingWithRetry(context.Background(), repo, &UsageBillingCommand{RequestID: "r1", APIKeyID: 1})
	require.ErrorIs(t, err, context.DeadlineExceeded)
	require.Equal(t, 1, repo.calls)
}

// 持久性瞬时错误重试到上限（3 次）后返回错误。
func TestApplyUsageBillingWithRetry_PersistentExhaustsAttempts(t *testing.T) {
	repo := &scriptedUsageBillingRepo{errs: []error{errors.New("x"), errors.New("x"), errors.New("x")}}
	_, err := applyUsageBillingWithRetry(context.Background(), repo, &UsageBillingCommand{RequestID: "r1", APIKeyID: 1})
	require.Error(t, err)
	require.Equal(t, 3, repo.calls)
}
