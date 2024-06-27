var zScoreChart; // Global variable to hold the chart instance

document.addEventListener('DOMContentLoaded', function() {
    // Initialize the chart when the page loads with empty data
    initializeChart();
    // Set up initial data fetch and subsequent updates
    updateData();
    setInterval(updateData, 5000); // Update data every 5 seconds
});

function initializeChart(zScoreData = []) {
    if (zScoreChart) {
        zScoreChart.destroy(); // Destroy the existing chart instance if it exists
    }
    const ctx = document.getElementById('zScoreChart').getContext('2d');
    zScoreChart = new Chart(ctx, {
        type: 'line',
        data: {
            labels: zScoreData.map(data => data.date),
            datasets: [{
                label: 'Z-Score',
                data: zScoreData.map(data => data.z_score),
                borderColor: 'rgb(75, 192, 192)',
                tension: 0.1
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: true, // Maintain aspect ratio
            aspectRatio: 3, // Aspect ratio of 3:1
            scales: {
                y: {
                    beginAtZero: false
                }
            }
        }
    });
}

function updateData() {
    const selectedPair = document.getElementById('pair-selector').value;
    fetch(`/update_chart?pair=${selectedPair}`) // Flask endpoint to fetch data
        .then(response => response.json())
        .then(data => {
            // Check if chart exists, destroy it and reinitialize to prevent resizing issues
            if (zScoreChart) {
                zScoreChart.destroy();
            }
            initializeChart(data); // Reinitialize the chart with new data
            updateDataTable(data); // Call the function to update the table data
        })
        .catch(error => console.error('Error updating chart:', error));
}

function updateDataTable(data) {
    const tableBody = document.getElementById('zScoreTable');
    tableBody.innerHTML = '<tr><th>Date</th><th>Z-Score</th></tr>'; // Reset the table and add headers

    data.forEach(score => {
        let row = tableBody.insertRow();
        let dateCell = row.insertCell(0);
        let scoreCell = row.insertCell(1);
        dateCell.textContent = score.date;
        scoreCell.textContent = score.z_score;
    });
}