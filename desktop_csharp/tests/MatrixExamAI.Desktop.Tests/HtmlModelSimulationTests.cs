using System;
using System.Linq;
using System.Threading;
using FluentAssertions;
using MatrixExamAI.Desktop.Views;
using MatrixExamAI.Shared.AI;
using MatrixExamAI.Shared.HtmlModel;
using Xunit;

namespace MatrixExamAI.Desktop.Tests
{
    public class HtmlModelSimulationTests
    {
        [Fact]
        public void HtmlModelCodeExtractor_ExtractFromMarkdown_ShouldExtractStandaloneHtml()
        {
            string md = @"Dưới đây là mã mô hình:
```html
<!DOCTYPE html>
<html>
<head><title>Test</title></head>
<body><h1>Hello 3D</h1></body>
</html>
```
Chúc bạn thành công!";

            string extracted = HtmlModelCodeExtractor.ExtractHtmlCode(md);
            extracted.Should().StartWith("<!DOCTYPE html>");
            extracted.Should().EndWith("</html>");
            extracted.Should().Contain("Hello 3D");
        }

        [Fact]
        public void HtmlModelCodeExtractor_ExtractFromRawDoctype_ShouldReturnCleanHtml()
        {
            string raw = "Lập trình xong <!DOCTYPE html><html><head><title>Test</title></head><body>OK</body></html> xong rồi nhé.";
            string extracted = HtmlModelCodeExtractor.ExtractHtmlCode(raw);
            extracted.Should().StartWith("<!DOCTYPE html>");
            extracted.Should().EndWith("</html>");
        }

        [Fact]
        public void HtmlModelCodeExtractor_WrapSnippet_ShouldIncludeThreeAndKatex()
        {
            string snippet = "<div id=\"canvas3D\"></div><script>const scene = new THREE.Scene();</script>";
            string extracted = HtmlModelCodeExtractor.ExtractHtmlCode(snippet);

            extracted.Should().StartWith("<!DOCTYPE html>");
            extracted.Should().Contain("three.js");
            extracted.Should().Contain("katex");
            extracted.Should().Contain("tailwindcss.com");
            extracted.Should().Contain("renderMathInElement");
        }

        [Fact]
        public void HtmlModelTemplateLibrary_GetAllTemplates_ShouldReturnCompleteList()
        {
            var templates = HtmlModelTemplateLibrary.GetAllTemplates();
            templates.Should().NotBeNullOrEmpty();
            templates.Count.Should().BeGreaterOrEqualTo(7);

            foreach (var t in templates)
            {
                t.Id.Should().NotBeNullOrWhiteSpace();
                t.Title.Should().NotBeNullOrWhiteSpace();
                t.Category.Should().NotBeNullOrWhiteSpace();
                t.HtmlCode.Should().NotBeNullOrWhiteSpace();
                t.HtmlCode.Should().Contain("three.js", "Mọi mô hình 3D đều phải nhúng Three.js");
            }
        }

        [Fact]
        public void HtmlModelTemplateLibrary_SolidOfRevolution_ShouldContainThreeLatheAndKatex()
        {
            var item = HtmlModelTemplateLibrary.GetTemplateSolidOfRevolution();
            item.Id.Should().Be("solid_rev_cau6");
            item.HtmlCode.Should().Contain("LatheGeometry", "Mô hình khối tròn xoay dùng Three.js LatheGeometry");
            item.HtmlCode.Should().Contain("canvas2D", "Có panel vẽ hình phẳng 2D gạch chéo");
            item.HtmlCode.Should().Contain("step-card", "Có các card bước giải chi tiết sư phạm");
            item.HtmlCode.Should().Contain("katex", "Có tích hợp KaTeX");
        }

        [Fact]
        public void HtmlModelTemplateLibrary_AllCategories_ShouldHaveTemplates()
        {
            var categories = HtmlModelTemplateLibrary.Categories;
            categories.Should().NotBeEmpty();

            var templates = HtmlModelTemplateLibrary.GetAllTemplates();
            var usedCategories = templates.Select(t => t.Category).Distinct().ToList();

            usedCategories.Should().Contain(c => c.Contains("Khối tròn xoay"));
            usedCategories.Should().Contain(c => c.Contains("Hình không gian"));
            usedCategories.Should().Contain(c => c.Contains("Tọa độ không gian Oxyz"));
            usedCategories.Should().Contain(c => c.Contains("Vật lý"));
            usedCategories.Should().Contain(c => c.Contains("Hóa học"));
            usedCategories.Should().Contain(c => c.Contains("Sinh học"));
        }

        [Fact]
        public void PromptCatalog_HtmlModelSystemPrompt_ShouldContainKeyInvariants()
        {
            string systemPrompt = PromptCatalog.HtmlModelSystemPrompt;
            systemPrompt.Should().NotBeNullOrWhiteSpace();
            systemPrompt.Should().Contain("Three.js");
            systemPrompt.Should().Contain("Tailwind CSS");
            systemPrompt.Should().Contain("KaTeX");
            systemPrompt.Should().Contain("STANDALONE");
            systemPrompt.Should().Contain("SPLIT VIEW");
        }

        [Fact]
        public void PromptCatalog_GetHtmlModelPrompt_ShouldIncludeCategoryAndInstructions()
        {
            string prompt = PromptCatalog.GetHtmlModelPrompt("Khối chóp S.ABC có đáy là tam giác vuông", "Hình không gian 3D", hasImage: true);
            prompt.Should().Contain("Hình không gian 3D");
            prompt.Should().Contain("Khối chóp S.ABC");
            prompt.Should().Contain("ẢNH MINH HỌA ĐÍNH KÈM");
        }

        [Fact]
        public void PromptCatalog_GetHtmlModelEditPrompt_ShouldIncludeOriginalCodeAndRequest()
        {
            string currentHtml = "<html><body>Original</body></html>";
            string editReq = "Đổi màu khối chóp sang màu tím và thêm nhãn đỉnh";
            string prompt = PromptCatalog.GetHtmlModelEditPrompt(currentHtml, editReq, hasImage: false);

            prompt.Should().Contain("Original");
            prompt.Should().Contain("Đổi màu khối chóp sang màu tím");
        }

        [Fact]
        public void HtmlModelView_CreationOnSta_ShouldHaveTemplatesAndSplitMode()
        {
            Exception? error = null;
            var thread = new Thread(() =>
            {
                try
                {
                    var view = new HtmlModelView();
                    view.Should().NotBeNull();
                    view.SetLayoutMode(HtmlModelLayoutMode.Split);
                    view.SetLayoutMode(HtmlModelLayoutMode.ModelOnly);
                    view.SetLayoutMode(HtmlModelLayoutMode.CodeOnly);
                    view.SetLayoutMode(HtmlModelLayoutMode.Split);
                }
                catch (Exception ex)
                {
                    error = ex;
                }
            });

            thread.SetApartmentState(ApartmentState.STA);
            thread.Start();
            thread.Join();

            error.Should().BeNull();
        }

        [Fact]
        public void MainWindow_HtmlModelNavigation_ShouldSetContentToHtmlModelView()
        {
            Exception? error = null;
            var thread = new Thread(() =>
            {
                try
                {
                    var win = new MainWindow();
                    win.NavigateTo("html_model");
                    win.CurrentNavigationTag.Should().Be("html_model");
                    win.MainContentFrame.Content.Should().BeSameAs(win.HtmlModelView);
                    win.Close();
                }
                catch (Exception ex)
                {
                    error = ex;
                }
            });

            thread.SetApartmentState(ApartmentState.STA);
            thread.Start();
            thread.Join();

            error.Should().BeNull();
        }
    }
}
