using System;
using System.Collections.Generic;
using System.Linq;
using FluentAssertions;
using MatrixExamAI.Shared.Tikz;
using MatrixExamAI.Shared.Validation;
using Xunit;

namespace MatrixExamAI.Desktop.Tests.Tikz
{
    public class TikzTemplateLibraryTests
    {
        [Fact]
        public void Categories_ShouldContainFiveCoreCategories()
        {
            // Arrange & Act
            var categories = TikzTemplateLibrary.Categories;

            // Assert
            categories.Should().NotBeNull();
            categories.Count.Should().Be(5, "Library must contain exactly 5 core pedagogical categories");

            var categoryIds = categories.Select(c => c.Id).ToList();
            categoryIds.Should().Contain(new[] { "plane_2d", "solid_3d", "graphs", "tables", "misc" });

            // Verify mapping to 2D, 3D, Graphs, Tables, Charts
            categories.Should().Contain(c => c.Id == "plane_2d" && c.Name.Contains("2D"));
            categories.Should().Contain(c => c.Id == "solid_3d" && c.Name.Contains("3D"));
            categories.Should().Contain(c => c.Id == "graphs" && c.Name.Contains("Đồ thị"));
            categories.Should().Contain(c => c.Id == "tables" && c.Name.Contains("tkz-tab"));
            categories.Should().Contain(c => c.Id == "misc" && c.Name.Contains("Biểu đồ"));
        }

        [Fact]
        public void Categories_AllCategories_ShouldHaveValidIdNameAndIcon()
        {
            // Arrange & Act
            var categories = TikzTemplateLibrary.Categories;

            // Assert
            foreach (var category in categories)
            {
                category.Id.Should().NotBeNullOrWhiteSpace($"Category Id must not be null/empty");
                category.Name.Should().NotBeNullOrWhiteSpace($"Category Name must not be null/empty for category '{category.Id}'");
                category.Icon.Should().NotBeNullOrWhiteSpace($"Category Icon must not be null/empty for category '{category.Id}'");
                category.Templates.Should().NotBeNull($"Category Templates list must not be null for category '{category.Id}'");
                category.Templates.Should().NotBeEmpty($"Category '{category.Id}' must contain at least one template");
            }
        }

        [Fact]
        public void AllTemplates_ShouldHaveAtLeast40AuthenticTemplates()
        {
            // Arrange & Act
            var allTemplates = TikzTemplateLibrary.AllTemplates;

            // Assert
            allTemplates.Should().NotBeNull();
            allTemplates.Count.Should().BeGreaterOrEqualTo(40, "Library must contain at least 40 authentic TikZ templates");

            // Verify unique IDs across the entire library
            var templateIds = allTemplates.Select(t => t.Id).ToList();
            templateIds.Should().OnlyHaveUniqueItems("Every template in the library must have a unique Id");
        }

        [Fact]
        public void AllTemplates_EveryTemplate_ShouldHaveValidIdTitleAndEnclosedTikzCode()
        {
            // Arrange & Act
            var allTemplates = TikzTemplateLibrary.AllTemplates;

            // Assert
            foreach (var template in allTemplates)
            {
                template.Id.Should().NotBeNullOrWhiteSpace("Template Id must not be empty");
                template.Title.Should().NotBeNullOrWhiteSpace($"Template Title must not be empty for Id '{template.Id}'");
                template.CategoryId.Should().NotBeNullOrWhiteSpace($"Template CategoryId must not be empty for Id '{template.Id}'");
                template.CategoryName.Should().NotBeNullOrWhiteSpace($"Template CategoryName must not be empty for Id '{template.Id}'");
                template.Description.Should().NotBeNullOrWhiteSpace($"Template Description must not be empty for Id '{template.Id}'");

                template.Code.Should().NotBeNullOrWhiteSpace($"Template Code must not be empty for Id '{template.Id}'");
                template.Code.Should().Contain(@"\begin{tikzpicture}", $"Template '{template.Id}' must contain \\begin{{tikzpicture}}");
                template.Code.Should().Contain(@"\end{tikzpicture}", $"Template '{template.Id}' must contain \\end{{tikzpicture}}");
            }
        }

        [Fact]
        public void AllTemplates_EveryTemplate_ShouldHaveBalancedBraces()
        {
            // Arrange & Act
            var allTemplates = TikzTemplateLibrary.AllTemplates;

            // Assert
            var unbalancedCurly = new List<string>();
            var unbalancedSquare = new List<string>();

            foreach (var template in allTemplates)
            {
                int openCurly = template.Code.Count(c => c == '{');
                int closeCurly = template.Code.Count(c => c == '}');
                if (openCurly != closeCurly)
                {
                    unbalancedCurly.Add($"'{template.Id}' ({template.Title}): open={openCurly}, close={closeCurly}");
                }

                int openSquare = template.Code.Count(c => c == '[');
                int closeSquare = template.Code.Count(c => c == ']');
                if (openSquare != closeSquare)
                {
                    unbalancedSquare.Add($"'{template.Id}' ({template.Title}): open={openSquare}, close={closeSquare}");
                }
            }

            unbalancedCurly.Should().BeEmpty(
                "All templates must have balanced curly braces { }: " + string.Join("; ", unbalancedCurly));
            unbalancedSquare.Should().BeEmpty(
                "All templates must have balanced square brackets [ ]: " + string.Join("; ", unbalancedSquare));
        }

        [Fact]
        public void RetrievalByCategory_ShouldGroupTemplatesCorrectly()
        {
            // Arrange & Act
            var categories = TikzTemplateLibrary.Categories;
            var allTemplates = TikzTemplateLibrary.AllTemplates;

            // Assert
            int totalGrouped = 0;
            foreach (var cat in categories)
            {
                cat.Templates.Should().NotBeEmpty($"Category '{cat.Id}' must have templates");
                foreach (var tpl in cat.Templates)
                {
                    tpl.CategoryId.Should().Be(cat.Id, $"Template '{tpl.Id}' CategoryId must match parent category '{cat.Id}'");
                    allTemplates.Should().Contain(t => t.Id == tpl.Id);
                }
                totalGrouped += cat.Templates.Count;
            }

            totalGrouped.Should().Be(allTemplates.Count, "Sum of category templates must equal total templates in library");
        }

        [Theory]
        [InlineData("tri_right", "Tam giác vuông")]
        [InlineData("cone", "nón")]
        [InlineData("graph_cubic", "bậc")]
        [InlineData("bbt_cubic_pos", "bậc")]
        [InlineData("chart_bar", "Biểu đồ cột")]
        public void FindById_WithExistingId_ShouldReturnMatchingTemplate(string id, string expectedTitlePart)
        {
            // Act
            var template = TikzTemplateLibrary.FindById(id);

            // Assert
            template.Should().NotBeNull($"Template with id '{id}' must exist in library");
            template!.Id.Should().Be(id);
            template.Title.Should().ContainEquivalentOf(expectedTitlePart);
            template.Code.Should().Contain(@"\begin{tikzpicture}");
        }

        [Theory]
        [InlineData(null)]
        [InlineData("")]
        [InlineData("   ")]
        [InlineData("non_existent_template_xyz_123")]
        public void FindById_WithInvalidOrMissingId_ShouldReturnNull(string? id)
        {
            // Act
            var template = TikzTemplateLibrary.FindById(id!);

            // Assert
            template.Should().BeNull();
        }

        [Fact]
        public void FindByTitle_WithExistingAndNonExistentTitle_ShouldWorkCorrectly()
        {
            // Arrange
            string validTitle = "Tam giác vuông ABC tại A";

            // Act
            var template = TikzTemplateLibrary.FindByTitle(validTitle);
            var missing = TikzTemplateLibrary.FindByTitle("Tiêu đề không tồn tại trong thư viện 9999");
            var nullResult = TikzTemplateLibrary.FindByTitle(null!);

            // Assert
            template.Should().NotBeNull();
            template!.Id.Should().Be("tri_right");

            missing.Should().BeNull();
            nullResult.Should().BeNull();
        }

        [Theory]
        [InlineData("tam giác", 3)]
        [InlineData("chóp", 3)]
        [InlineData("3D", 5)]
        [InlineData("đồ thị", 5)]
        [InlineData("bảng biến thiên", 3)]
        public void Search_WithKeywords_ShouldReturnMatchingTemplates(string query, int minimumExpected)
        {
            // Act
            var results = TikzTemplateLibrary.Search(query);

            // Assert
            results.Should().NotBeNull();
            results.Count.Should().BeGreaterOrEqualTo(minimumExpected,
                $"Search for '{query}' should return at least {minimumExpected} templates");
        }

        [Fact]
        public void Search_WithEmptyOrNull_ShouldReturnAllTemplates()
        {
            // Act
            var emptyResults = TikzTemplateLibrary.Search("");
            var whitespaceResults = TikzTemplateLibrary.Search("   ");
            var nullResults = TikzTemplateLibrary.Search(null!);

            // Assert
            int total = TikzTemplateLibrary.AllTemplates.Count;
            emptyResults.Count.Should().Be(total);
            whitespaceResults.Count.Should().Be(total);
            nullResults.Count.Should().Be(total);
        }

        [Fact]
        public void AllTemplates_PreflightCheck_ShouldHaveZeroBlockingErrors()
        {
            // Arrange & Act
            var allTemplates = TikzTemplateLibrary.AllTemplates;
            var errorTemplates = new List<string>();

            // Assert
            foreach (var template in allTemplates)
            {
                var issues = TikzPreflightValidator.Check(template.Code);
                var blockingErrors = issues.Where(i => i.Severity == IssueSeverity.Error).ToList();
                if (blockingErrors.Any())
                {
                    errorTemplates.Add($"'{template.Id}': {string.Join(", ", blockingErrors.Select(e => e.Message))}");
                }
            }

            errorTemplates.Should().BeEmpty(
                "All authentic templates in library must pass TikzPreflightValidator with zero blocking errors: " +
                string.Join("; ", errorTemplates));
        }

        [Theory]
        [InlineData("pyramid_regular_tri", "chóp tam giác đều")]
        [InlineData("tetrahedron_regular", "Tứ diện đều")]
        [InlineData("pyramid_frustum", "chóp cụt")]
        [InlineData("cube_diagonal", "lập phương")]
        [InlineData("cylinder_section", "thiết diện qua trục")]
        [InlineData("cone_frustum", "nón cụt")]
        [InlineData("sphere_circum_cube", "mặt cầu ngoại tiếp")]
        [InlineData("octahedron_regular", "bát diện đều")]
        [InlineData("coord_3d_oxyz", "Oxyz")]
        [InlineData("sphere_plane_section", "thiết diện tròn")]
        [InlineData("cone_vertex_section", "thiết diện qua đỉnh")]
        [InlineData("cylinder_parallel_section", "song song với trục")]
        [InlineData("spherical_cap", "chỏm cầu")]
        [InlineData("cylinder_inscribed_cone", "trụ nội tiếp")]
        [InlineData("sphere_circum_cylinder", "cầu ngoại tiếp")]
        [InlineData("solid_of_revolution_parabola", "Parabol")]
        public void Solid3D_AdvancedShapes_ShouldExistAndBeValid(string id, string expectedTitlePart)
        {
            var template = TikzTemplateLibrary.FindById(id);
            template.Should().NotBeNull($"Shape '{id}' must exist in solid_3d category");
            template!.CategoryId.Should().Be("solid_3d");
            template.Title.Should().ContainEquivalentOf(expectedTitlePart);
            template.Code.Should().Contain(@"\begin{tikzpicture}");
            template.Code.Should().Contain(@"\end{tikzpicture}");
        }

        [Fact]
        public void LoadUserFigures_PopulatesUserCategoryWithoutMutatingCoreCategories()
        {
            // Arrange
            var testFigures = new List<(string Id, string Title, string Description, IEnumerable<string> Tags, string Code)>
            {
                ("test_01", "Hình Test 01", "Mô tả test", new[] { "tag1" }, @"\begin{tikzpicture}\draw (0,0)--(1,1);\end{tikzpicture}")
            };

            // Act
            TikzTemplateLibrary.LoadUserFigures(testFigures);

            // Assert
            TikzTemplateLibrary.Categories.Count.Should().Be(5);
            TikzTemplateLibrary.UserFiguresCategory.Templates.Count.Should().Be(1);
            TikzTemplateLibrary.UserFiguresCategory.Templates[0].Title.Should().Be("Hình Test 01");
        }
    }
}
