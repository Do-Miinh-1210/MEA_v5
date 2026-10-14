#include <cstddef>
#include <cstdint>
#include <cstring>

#if defined(_WIN32)
#define MEA_EXPORT extern "C" __declspec(dllexport)
#else
#define MEA_EXPORT extern "C" __attribute__((visibility("default")))
#endif

namespace {

bool is_space(const char ch) {
    return ch == ' ' || ch == '\t' || ch == '\r' || ch == '\n'
        || ch == '\f' || ch == '\v';
}

char upper_ascii(const char ch) {
    return (ch >= 'a' && ch <= 'z') ? static_cast<char>(ch - ('a' - 'A')) : ch;
}

bool match_marker(
    const char* text,
    const std::size_t len,
    const std::size_t pos,
    const char* word,
    std::size_t* end_pos
) {
    std::size_t cursor = pos;
    if (cursor + 3 > len || std::memcmp(text + cursor, "===", 3) != 0) {
        return false;
    }
    cursor += 3;
    while (cursor < len && is_space(text[cursor])) {
        ++cursor;
    }
    for (std::size_t i = 0; word[i] != '\0'; ++i) {
        if (cursor >= len || upper_ascii(text[cursor]) != word[i]) {
            return false;
        }
        ++cursor;
    }
    while (cursor < len && is_space(text[cursor])) {
        ++cursor;
    }
    if (cursor + 3 > len || std::memcmp(text + cursor, "===", 3) != 0) {
        return false;
    }
    *end_pos = cursor + 3;
    return true;
}

}  // namespace

MEA_EXPORT std::uint32_t mea_native_abi_version() {
    return 1;
}

MEA_EXPORT std::size_t mea_find_exact_blocks_utf8(
    const char* text,
    const std::size_t len,
    std::size_t* starts,
    std::size_t* ends,
    const std::size_t capacity
) {
    if (text == nullptr || len == 0) {
        return 0;
    }

    std::size_t count = 0;
    std::size_t cursor = 0;
    while (cursor < len) {
        std::size_t content_start = 0;
        if (!match_marker(text, len, cursor, "CAU", &content_start)) {
            ++cursor;
            continue;
        }

        std::size_t close_cursor = content_start;
        std::size_t close_end = 0;
        while (close_cursor < len
               && !match_marker(text, len, close_cursor, "KETCAU", &close_end)) {
            ++close_cursor;
        }
        if (close_cursor >= len) {
            break;
        }

        if (count < capacity && starts != nullptr && ends != nullptr) {
            starts[count] = content_start;
            ends[count] = close_cursor;
        }
        ++count;
        cursor = close_end;
    }
    return count;
}

MEA_EXPORT std::size_t mea_collapse_blank_lines_utf8(
    const char* text,
    const std::size_t len,
    char* output,
    const std::size_t capacity
) {
    if (text == nullptr || len == 0) {
        return 0;
    }

    std::size_t out_len = 0;
    std::size_t last_non_space = 0;
    bool started = false;
    const auto emit = [&](const char ch) {
        if (!started && is_space(ch)) {
            return;
        }
        started = true;
        if (output != nullptr && out_len < capacity) {
            output[out_len] = ch;
        }
        ++out_len;
        if (!is_space(ch)) {
            last_non_space = out_len;
        }
    };

    bool previous_blank = false;
    std::size_t line_start = 0;
    while (line_start <= len) {
        std::size_t line_end = line_start;
        while (line_end < len && text[line_end] != '\n') {
            ++line_end;
        }

        bool blank = true;
        for (std::size_t i = line_start; i < line_end; ++i) {
            if (!is_space(text[i])) {
                blank = false;
                break;
            }
        }
        if (!(blank && previous_blank)) {
            for (std::size_t i = line_start; i < line_end; ++i) {
                emit(text[i]);
            }
            if (line_end < len) {
                emit('\n');
            }
        }
        previous_blank = blank;
        if (line_end >= len) {
            break;
        }
        line_start = line_end + 1;
    }

    return last_non_space;
}
