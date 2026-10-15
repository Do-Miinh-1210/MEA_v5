using System.Windows;

namespace MatrixExamAI.Desktop.Views
{
    public partial class QuickGuideDialog : Window
    {
        public QuickGuideDialog()
        {
            InitializeComponent();
        }

        private void BtnClose_Click(object sender, RoutedEventArgs e)
        {
            Close();
        }
    }
}
