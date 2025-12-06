<!--
1. Add this code to a new HTML card in your Ghost editor.
2. Make sure your Flask app is running and accessible from the internet.
   If you are running it locally, you can use a tool like ngrok to expose it to the internet.
-->

<!-- 1. Include Plotly.js -->
<script src="https://cdn.plot.ly/plotly-latest.min.js"></script>

<!-- 2. Create a div to host the chart -->
<div id="plotly-chart"></div>

<!-- 3. Fetch data and render the chart -->
<script>
  // Replace with the actual URL of your Flask app
  const url = '0.0.0.0:8050/api/philippine_sardines';

  fetch(url)
    .then(response => response.json())
    .then(figure => {
      // The JSON response from the API is a Plotly figure object.
      // We can pass it directly to Plotly.newPlot().
      const chartDiv = document.getElementById('plotly-chart');
      Plotly.newPlot(chartDiv, figure.data, figure.layout);
    })
    .catch(error => {
      console.error('Error fetching data for Plotly chart:', error);
      const chartDiv = document.getElementById('plotly-chart');
      chartDiv.innerHTML = 'Error loading chart. Please check the console for details.';
    });
</script>
