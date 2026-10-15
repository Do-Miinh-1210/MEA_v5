using System.Windows;
using System.Windows.Controls;

namespace MatrixExamAI.Desktop.Views
{
    public partial class AiMatrixDialog : Window
    {
        public string Subject { get; private set; } = "Toán";
        public string Grade { get; private set; } = "12";
        public string Duration { get; private set; } = "45 phút";
        public string Semester { get; private set; } = "I";
        public string ExtraRequirements { get; private set; } = string.Empty;

        public AiMatrixDialog()
        {
            InitializeComponent();
        }

        private void BtnGenerate_Click(object sender, RoutedEventArgs e)
        {
            Subject = (CmbSubject.SelectedItem as ComboBoxItem)?.Content?.ToString() ?? "Toán";
            Grade = (CmbGrade.SelectedItem as ComboBoxItem)?.Content?.ToString() ?? "12";
            Duration = (CmbDuration.SelectedItem as ComboBoxItem)?.Content?.ToString() ?? "45 phút";
            Semester = (CmbSemester.SelectedItem as ComboBoxItem)?.Content?.ToString() ?? "I";
            ExtraRequirements = TxtExtraRequirements.Text.Trim();

            DialogResult = true;
            Close();
        }

        private void BtnCancel_Click(object sender, RoutedEventArgs e)
        {
            DialogResult = false;
            Close();
        }
    }
}
