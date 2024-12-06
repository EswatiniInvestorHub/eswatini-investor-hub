function createHistogram(priceHistoryData) {
    const ctx = document.getElementById("share-price-chart").getContext("2d");

    // Format data for the chart
    const labels = priceHistoryData.map(item => item.date);
    const prices = priceHistoryData.map(item => item.price);

    // Destroy existing chart instance if any
    if (window.sharePriceChart) {
        window.sharePriceChart.destroy();
    }

    // Create a new histogram
    window.sharePriceChart = new Chart(ctx, {
        type: 'bar',
        data: {
            labels: labels,
            datasets: [{
                label: 'Share Price (E)',
                data: prices,
                backgroundColor: 'rgba(54, 162, 235, 0.6)',
                borderColor: 'rgba(54, 162, 235, 1)',
                borderWidth: 1
            }]
        },
        options: {
            scales: {
                x: {
                    title: {
                        display: true,
                        text: 'Date'
                    }
                },
                y: {
                    title: {
                        display: true,
                        text: 'Price (E)'
                    },
                    beginAtZero: false
                }
            }
        }
    });
}
