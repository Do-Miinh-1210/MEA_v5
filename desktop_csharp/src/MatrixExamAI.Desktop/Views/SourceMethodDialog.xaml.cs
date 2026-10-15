using System.Windows;
using System.Windows.Controls;
using System.Windows.Input;

namespace MatrixExamAI.Desktop.Views
{
    public partial class SourceMethodDialog : Window
    {
        public string SelectedMode { get; private set; } = "ai_only"; // "ai_only", "bank_only", "mixed"
        public int BankRatio { get; private set; } = 50;

        public SourceMethodDialog()
        {
            InitializeComponent();
        }

        private void Card1_MouseLeftButtonDown(object sender, MouseButtonEventArgs e)
        {
            RbAiOnly.IsChecked = true;
        }

        private void Card2_MouseLeftButtonDown(object sender, MouseButtonEventArgs e)
        {
            RbBankOnly.IsChecked = true;
        }

        private void Card3_MouseLeftButtonDown(object sender, MouseButtonEventArgs e)
        {
            RbMixed.IsChecked = true;
        }

        private void BtnConfirm_Click(object sender, RoutedEventArgs e)
        {
            if (RbBankOnly.IsChecked == true)
            {
                SelectedMode = "bank_only";
                BankRatio = 100;
            }
            else if (RbMixed.IsChecked == true)
            {
                SelectedMode = "mixed";
                if (CmbBankRatio.SelectedItem is ComboBoxItem item && int.TryParse(item.Tag?.ToString(), out int r))
                {
                    BankRatio = r;
                }
                else
                {
                    BankRatio = 50;
                }
            }
            else
            {
                SelectedMode = "ai_only";
                BankRatio = 0;
            }

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
