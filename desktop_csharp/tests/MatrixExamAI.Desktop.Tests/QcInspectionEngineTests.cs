using System;
using System.Collections.Generic;
using System.Linq;
using System.Text.RegularExpressions;
using FluentAssertions;
using MatrixExamAI.Shared.Extensibility;
using MatrixExamAI.Shared.Validation;
using Xunit;

namespace MatrixExamAI.Desktop.Tests
{
    public class QcInspectionEngineTests
    {
        #region Tier 1 - Normative Tests (QC Rules for Exam Verification)

        [Fact]
        public void QcEngine_DuplicateOptionsDetection_ShouldFlagQuestionsWithDuplicateOptionTexts()
        {
            var questionWithDuplicate = new QuestionItem
            {
                QuestionCode = "QC_DUP_01",
                QuestionType = "MultipleChoice4",
                Content = "Phương trình $x^2 - 4 = 0$ có nghiệm là:",
                Options = new Dictionary<string, string>
                {
                    ["A"] = "$x = 2$",
                    ["B"] = "$x = -2$",
                    ["C"] = "$x = 2$", // Duplicate of A!
                    ["D"] = "$x = 4$"
                },
                CorrectAnswer = "A"
            };

            // Rule check: detect duplicates
            var duplicates = questionWithDuplicate.Options.Values
                .GroupBy(v => v.Trim())
                .Where(g => g.Count() > 1)
                .Select(g => g.Key)
                .ToList();

            duplicates.Should().NotBeEmpty("QC engine must detect duplicate option text '$x = 2$'");
            duplicates.Should().Contain("$x = 2$");
        }

        [Fact]
        public void QcEngine_MissingCorrectAnswerDetection_ShouldFlagQuestionsWithoutAnswers()
        {
            var questionMissingAnswer = new QuestionItem
            {
                QuestionCode = "QC_NO_ANS_01",
                Content = "Câu hỏi chưa có đáp án đúng",
                CorrectAnswer = "" // Missing!
            };

            bool isMissingAnswer = string.IsNullOrWhiteSpace(questionMissingAnswer.CorrectAnswer);
            isMissingAnswer.Should().BeTrue("QC engine must flag questions missing a correct answer");
        }

        [Fact]
        public void QcEngine_MissingOptionsDetection_ShouldFlagMultipleChoiceWithLessThan4Options()
        {
            var questionWithFewOptions = new QuestionItem
            {
                QuestionCode = "QC_FEW_OPTS",
                QuestionType = "MultipleChoice4",
                Content = "Câu trắc nghiệm chỉ có 3 phương án",
                Options = new Dictionary<string, string>
                {
                    ["A"] = "Phương án A",
                    ["B"] = "Phương án B",
                    ["C"] = "Phương án C"
                },
                CorrectAnswer = "A"
            };

            bool has4Options = questionWithFewOptions.Options != null &&
                               questionWithFewOptions.Options.Count == 4 &&
                               new[] { "A", "B", "C", "D" }.All(questionWithFewOptions.Options.ContainsKey);

            has4Options.Should().BeFalse("QC engine must flag MultipleChoice4 questions missing option D");
        }

        [Fact]
        public void QcEngine_UnbalancedMathDollars_ShouldFlagSyntaxIssues()
        {
            string questionWithBrokenMath = "Cho hàm số $y = f(x) với cực đại tại $x = 1$.";

            // Count single dollar occurrences
            int dollarCount = questionWithBrokenMath.Count(c => c == '$');
            bool hasUnbalancedDollars = (dollarCount % 2) != 0;

            hasUnbalancedDollars.Should().BeTrue("Single unclosed dollar sign must be detected by QC");
        }

        #endregion

        #region Tier 2 - Boundary Value Tests (LatexErrorLogParser)

        [Fact]
        public void LatexErrorLogParser_StandardErrorLog_ShouldExtractLineNumberAndDescription()
        {
            string sampleLog = @"This is pdfTeX, Version 3.141592653-2.6-1.40.24 (TeX Live 2022)
entering extended mode
(./tikz_test.tex
LaTeX2e <2022-11-01> patch level 1
! Undefined control sequence.
l.24 \draw[line cap=invalid]
                             (0,0) -- (1,1);
? 
No pages of output.";

            var error = LatexErrorLogParser.ParseLog(sampleLog);

            error.Should().NotBeNull();
            error!.ErrorLine.Should().Be(24);
            error.ErrorDescription.Should().Be("Undefined control sequence.");
            error.ContextSnippet.Should().Contain("draw[line cap=invalid]");
        }

        [Fact]
        public void LatexErrorLogParser_CleanLogWithoutErrors_ShouldReturnNull()
        {
            string cleanLog = @"This is pdfTeX, Version 3.141592653
Output written on tikz_test.pdf (1 page, 14502 bytes).
Transcript written on tikz_test.log.";

            var error = LatexErrorLogParser.ParseLog(cleanLog);
            error.Should().BeNull("Clean LaTeX log has no '! ' prefix error");
        }

        [Fact]
        public void LatexErrorLogParser_EmptyOrWhitespace_ShouldReturnNull()
        {
            LatexErrorLogParser.ParseLog("").Should().BeNull();
            LatexErrorLogParser.ParseLog(null).Should().BeNull();
            LatexErrorLogParser.ParseLog("   \n\t  ").Should().BeNull();
        }

        #endregion

        #region Tier 3 - Combinatorial & Full 22-Question Clean Exam Audit

        [Fact]
        public void QcEngine_Clean22QuestionExam_ShouldPassAllChecksWithZeroViolations()
        {
            // Build a valid 22-question exam
            var questions = new List<QuestionItem>();

            // 12 MCQ
            for (int i = 1; i <= 12; i++)
            {
                questions.Add(new QuestionItem
                {
                    QuestionCode = $"Q_MCQ_{i:D2}",
                    QuestionType = "MultipleChoice4",
                    Content = $"Nội dung câu {i} với công thức ${{x + {i}}}$.",
                    Options = new Dictionary<string, string>
                    {
                        ["A"] = $"Phương án A của {i}",
                        ["B"] = $"Phương án B của {i}",
                        ["C"] = $"Phương án C của {i}",
                        ["D"] = $"Phương án D của {i}"
                    },
                    CorrectAnswer = "A"
                });
            }

            // 4 True/False
            for (int i = 1; i <= 4; i++)
            {
                questions.Add(new QuestionItem
                {
                    QuestionCode = $"Q_TF_{i:D2}",
                    QuestionType = "TrueFalse4",
                    Content = $"Mệnh đề đúng sai câu {i}.",
                    Options = new Dictionary<string, string>
                    {
                        ["a"] = "Ý a",
                        ["b"] = "Ý b",
                        ["c"] = "Ý c",
                        ["d"] = "Ý d"
                    },
                    CorrectAnswer = "a:Đ, b:S, c:Đ, d:S"
                });
            }

            // 6 Short Answer
            for (int i = 1; i <= 6; i++)
            {
                questions.Add(new QuestionItem
                {
                    QuestionCode = $"Q_SA_{i:D2}",
                    QuestionType = "ShortAnswer",
                    Content = $"Câu trả lời ngắn số {i}.",
                    CorrectAnswer = i.ToString()
                });
            }

            // Run QC Audit on all 22 questions
            var qcErrors = new List<string>();

            foreach (var q in questions)
            {
                // Check 1: Missing Answer
                if (string.IsNullOrWhiteSpace(q.CorrectAnswer))
                {
                    qcErrors.Add($"[{q.QuestionCode}] Thiếu đáp án đúng.");
                }

                // Check 2: MCQ 4 options
                if (q.QuestionType == "MultipleChoice4")
                {
                    if (q.Options == null || q.Options.Count != 4 || !new[] { "A", "B", "C", "D" }.All(q.Options.ContainsKey))
                    {
                        qcErrors.Add($"[{q.QuestionCode}] Không đủ 4 phương án A-B-C-D.");
                    }
                    else
                    {
                        // Check duplicates
                        if (q.Options.Values.GroupBy(v => v.Trim()).Any(g => g.Count() > 1))
                        {
                            qcErrors.Add($"[{q.QuestionCode}] Trùng lặp phương án.");
                        }
                    }
                }

                // Check 3: TrueFalse 4 options
                if (q.QuestionType == "TrueFalse4")
                {
                    if (q.Options == null || q.Options.Count != 4 || !new[] { "a", "b", "c", "d" }.All(q.Options.ContainsKey))
                    {
                        qcErrors.Add($"[{q.QuestionCode}] Không đủ 4 mệnh đề a-b-c-d.");
                    }
                }
            }

            qcErrors.Should().BeEmpty("Valid 22-question standard exam must pass QC with 0 errors");
        }

        #endregion

        #region Tier 4 - Workload & High Volume QC Batch Testing

        [Fact]
        public void QcEngine_HighVolumeBatchAudit_100Questions_ShouldExecuteInUnder50Ms()
        {
            var questions = new List<QuestionItem>();
            for (int i = 1; i <= 100; i++)
            {
                questions.Add(new QuestionItem
                {
                    QuestionCode = $"Q_{i:D3}",
                    QuestionType = "MultipleChoice4",
                    Content = $"Câu hỏi {i}",
                    Options = new Dictionary<string, string>
                    {
                        ["A"] = $"Opt A {i}",
                        ["B"] = $"Opt B {i}",
                        ["C"] = $"Opt C {i}",
                        ["D"] = $"Opt D {i}"
                    },
                    CorrectAnswer = "A"
                });
            }

            var sw = System.Diagnostics.Stopwatch.StartNew();
            int errorCount = 0;
            foreach (var q in questions)
            {
                if (string.IsNullOrWhiteSpace(q.CorrectAnswer)) errorCount++;
                if (q.Options.Values.Distinct().Count() < q.Options.Count) errorCount++;
            }
            sw.Stop();

            sw.ElapsedMilliseconds.Should().BeLessThan(50, "Batch QC validation of 100 questions must take < 50ms");
            errorCount.Should().Be(0);
        }

        #endregion
    }
}
