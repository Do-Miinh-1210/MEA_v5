using Xunit;

// Disable parallel test execution for WPF STA UI tests to prevent PackagePart/Application.LoadComponent race conditions
[assembly: CollectionBehavior(DisableTestParallelization = true)]
