using System;
using System.Collections.Generic;
using System.Linq;
using System.Net;

namespace MatrixExamAI.Shared.AI
{
    /// <summary>
    /// Trạng thái sức khỏe của API Key.
    /// </summary>
    public enum KeyState
    {
        /// <summary>
        /// Sẵn sàng thực thi yêu cầu.
        /// </summary>
        Active,

        /// <summary>
        /// Đang bị giới hạn tần suất (HTTP 429 Quota Exceeded), tự động phục hồi sau CooldownUntilUtc.
        /// </summary>
        RateLimited,

        /// <summary>
        /// Key không hợp lệ hoặc đã bị vô hiệu hóa (HTTP 400/401/403).
        /// </summary>
        Invalid
    }

    /// <summary>
    /// Bản ghi theo dõi một API Key trong pool.
    /// </summary>
    public class ApiKeyEntry
    {
        public string Key { get; set; } = string.Empty;
        public KeyState State { get; set; } = KeyState.Active;
        public DateTime CooldownUntilUtc { get; set; } = DateTime.MinValue;
        public int FailureCount { get; set; }
        public int SuccessCount { get; set; }
        public DateTime LastUsedUtc { get; set; } = DateTime.MinValue;

        public bool IsAvailable(DateTime nowUtc)
        {
            if (State == KeyState.Active)
            {
                return true;
            }

            if (State == KeyState.RateLimited && nowUtc >= CooldownUntilUtc)
            {
                State = KeyState.Active;
                return true;
            }

            return false;
        }

        public string MaskedKey
        {
            get
            {
                if (string.IsNullOrEmpty(Key)) return string.Empty;
                if (Key.Length <= 8) return "****";
                return Key.Substring(0, 4) + "..." + Key.Substring(Key.Length - 4);
            }
        }
    }

    /// <summary>
    /// Quản lý xoay vòng API Key (Round-robin), theo dõi trạng thái hạn mức và phục hồi sau cooldown.
    /// </summary>
    public class ApiKeyPoolManager
    {
        private readonly List<ApiKeyEntry> _keys = new List<ApiKeyEntry>();
        private int _currentIndex = 0;
        private readonly object _syncLock = new object();

        public ApiKeyPoolManager()
        {
        }

        public ApiKeyPoolManager(IEnumerable<string> initialKeys)
        {
            SetKeys(initialKeys);
        }

        /// <summary>
        /// Đặt lại toàn bộ danh sách keys (phân tách bởi dấu phẩy, chấm phẩy hoặc xuống dòng).
        /// </summary>
        public void SetKeys(IEnumerable<string>? keys)
        {
            lock (_syncLock)
            {
                _keys.Clear();
                _currentIndex = 0;
                if (keys != null)
                {
                    foreach (var k in keys)
                    {
                        AddKeyInternal(k);
                    }
                }
            }
        }

        /// <summary>
        /// Nạp chuỗi raw keys (có thể gồm nhiều keys phân tách bằng phẩy, chấm phẩy, khoảng trắng).
        /// </summary>
        public void LoadFromString(string? rawKeys)
        {
            if (string.IsNullOrWhiteSpace(rawKeys)) return;

            var split = rawKeys!.Split(new[] { ',', ';', '\r', '\n' }, StringSplitOptions.RemoveEmptyEntries);
            lock (_syncLock)
            {
                foreach (var s in split)
                {
                    AddKeyInternal(s.Trim());
                }
            }
        }

        /// <summary>
        /// Thêm một key mới vào pool.
        /// </summary>
        public void AddKey(string key)
        {
            if (string.IsNullOrWhiteSpace(key)) return;
            lock (_syncLock)
            {
                AddKeyInternal(key.Trim());
            }
        }

        private void AddKeyInternal(string key)
        {
            if (string.IsNullOrWhiteSpace(key)) return;
            if (_keys.Any(e => string.Equals(e.Key, key, StringComparison.Ordinal))) return;

            _keys.Add(new ApiKeyEntry
            {
                Key = key,
                State = KeyState.Active
            });
        }

        /// <summary>
        /// Lấy key khả dụng tiếp theo theo cơ chế Round-robin.
        /// </summary>
        public ApiKeyEntry? GetNextAvailableKey()
        {
            lock (_syncLock)
            {
                if (_keys.Count == 0) return null;

                var now = DateTime.UtcNow;
                for (int i = 0; i < _keys.Count; i++)
                {
                    var idx = (_currentIndex + i) % _keys.Count;
                    var entry = _keys[idx];

                    if (entry.IsAvailable(now))
                    {
                        entry.LastUsedUtc = now;
                        _currentIndex = (idx + 1) % _keys.Count;
                        return entry;
                    }
                }

                return null;
            }
        }

        /// <summary>
        /// Ghi nhận gọi thành công cho key.
        /// </summary>
        public void ReportSuccess(string key)
        {
            lock (_syncLock)
            {
                var entry = _keys.FirstOrDefault(k => string.Equals(k.Key, key, StringComparison.Ordinal));
                if (entry != null)
                {
                    entry.SuccessCount++;
                    entry.State = KeyState.Active;
                }
            }
        }

        /// <summary>
        /// Ghi nhận thất bại HTTP và chuyển trạng thái key sang Cooldown hoặc Invalid.
        /// </summary>
        public void ReportFailure(string key, HttpStatusCode statusCode, int? retryAfterSeconds = null)
        {
            lock (_syncLock)
            {
                var entry = _keys.FirstOrDefault(k => string.Equals(k.Key, key, StringComparison.Ordinal));
                if (entry == null) return;

                entry.FailureCount++;

                if (statusCode == (HttpStatusCode)429) // Too Many Requests
                {
                    int cooldown = retryAfterSeconds.HasValue && retryAfterSeconds.Value > 0
                        ? retryAfterSeconds.Value
                        : 60;

                    entry.State = KeyState.RateLimited;
                    entry.CooldownUntilUtc = DateTime.UtcNow.AddSeconds(cooldown);
                }
                else if (statusCode == HttpStatusCode.Unauthorized ||
                         statusCode == HttpStatusCode.Forbidden ||
                         statusCode == HttpStatusCode.BadRequest)
                {
                    entry.State = KeyState.Invalid;
                }
            }
        }

        /// <summary>
        /// Đếm tổng số key trong pool.
        /// </summary>
        public int TotalKeys
        {
            get
            {
                lock (_syncLock)
                {
                    return _keys.Count;
                }
            }
        }

        /// <summary>
        /// Đếm số key đang sẵn sàng hoạt động.
        /// </summary>
        public int ActiveKeys
        {
            get
            {
                lock (_syncLock)
                {
                    var now = DateTime.UtcNow;
                    return _keys.Count(k => k.IsAvailable(now));
                }
            }
        }

        /// <summary>
        /// Tóm tắt trạng thái của pool keys.
        /// </summary>
        public string GetStatusSummary()
        {
            lock (_syncLock)
            {
                var now = DateTime.UtcNow;
                int active = _keys.Count(k => k.IsAvailable(now));
                int limited = _keys.Count(k => k.State == KeyState.RateLimited && now < k.CooldownUntilUtc);
                int invalid = _keys.Count(k => k.State == KeyState.Invalid);
                return $"Tổng: {_keys.Count} keys (Khả dụng: {active}, Chờ hạn mức: {limited}, Không hợp lệ: {invalid})";
            }
        }
    }
}
