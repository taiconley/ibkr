var zScoreChart; // Global variable to hold the chart instance
var pricesChart;  // Global variable for the prices chart


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

function initializePriceChart(pricesData) {
    if (pricesChart) {
        pricesChart.destroy();  // Destroy existing chart instance if it exists
    }
    const ctx = document.getElementById('pricesChart').getContext('2d');
    pricesChart = new Chart(ctx, {
        type: 'line',
        data: {
            labels: pricesData.map(data => data.date),
            datasets: [{
                label: 'Close Stock 1',
                data: pricesData.map(data => data.close_stock1),
                borderColor: 'rgb(255, 99, 132)',
                fill: false,
                yAxisID: 'y-axis-1',
            }, {
                label: 'Close Stock 2',
                data: pricesData.map(data => data.close_stock2),
                borderColor: 'rgb(54, 162, 235)',
                fill: false,
                yAxisID: 'y-axis-2'
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: true,
            scales: {
                yAxes: [{
                    id: 'y-axis-1',
                    position: 'left',
                    ticks: {
                        beginAtZero: false
                    }
                }, {
                    id: 'y-axis-2',
                    position: 'right',
                    ticks: {
                        beginAtZero: false
                    },
                    gridLines: {
                        drawOnChartArea: false
                    }
                }]
            }
        }
    });
}


function updateData() {
    const selectedPair = document.getElementById('pair-selector').value;
    const scrollTop = window.scrollY;  // Save the current scroll position

    fetch(`/update_chart?pair=${selectedPair}`)  // Flask endpoint to fetch data
        .then(response => response.json())
        .then(data => {
            if (zScoreChart) {
                zScoreChart.destroy();
            }
            if (pricesChart) {
                pricesChart.destroy();
            }
            initializeChart(data.chartData);  // Reinitialize the z-score chart with new data
            initializePriceChart(data.prices);  // Reinitialize the prices chart with new data

            window.scrollTo(0, scrollTop);  // Restore the scroll position
        })
        .catch(error => console.error('Error updating charts:', error));
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