let currentIndex = 0;
const slides = document.querySelectorAll('.news-slide');
const totalSlides = slides.length;

// Function to show the current slide
function showSlide(index) {
    slides.forEach((slide, i) => {
        slide.style.display = i === index ? 'block' : 'none';
    });
}

// Function to go to the next slide
function nextSlide() {
    currentIndex = (currentIndex + 1) % totalSlides;
    showSlide(currentIndex);
}

// Function to go to the previous slide
function prevSlide() {
    currentIndex = (currentIndex - 1 + totalSlides) % totalSlides;
    showSlide(currentIndex);
}

const nextBtn = document.querySelector('.slider-nav.next');
if (nextBtn) {
  nextBtn.addEventListener('click', nextSlide);
}

const prevBtn = document.querySelector('.slider-nav.prev');
if (prevBtn) {
  prevBtn.addEventListener('click', prevSlide);
}


// Show the initial slide
showSlide(currentIndex);

// Automatic slide every 3 seconds
setInterval(nextSlide, 3000);

let chartInstance; // Keep track of Chart.js instance

// Function to show company details in the modal
async function showCompanyDetails(companyId) {
    try {
        // Fetch company data from the API
        const response = await fetch(`/api/company/${companyId}`);
        const data = await response.json();

        if (data.error) {
            alert(data.error);
            return;
        }

        // Populate modal content
        document.getElementById("company-title").innerText = data.name;
        document.getElementById("company-share-price").innerText = "Share Price: " + data.share_price;
        document.getElementById("company-market-cap").innerText = "Market Cap: " + data.market_cap;
        document.getElementById("company-stock-code").innerText = "Stock Code: " + data.stock_code;
        document.getElementById("company-listed-instruments").innerText = "Listed Instruments: " + data.listed_instruments;
        document.getElementById("company-website").innerText = "Company Website: " + data.website;
        document.getElementById("company-about").innerText = data.about;

        // Populate Latest News
        const latestNewsContainer = document.getElementById("latest-news");
        latestNewsContainer.innerHTML = "";
        data.latest_news.forEach(news => {
            const newsItem = document.createElement("div");
            newsItem.innerHTML = `
                <p><strong>${news.title}</strong></p>
                <p>${news.date}</p>
                <p>${news.content}</p>
                <a href="${news.link}">Read more</a>
            `;
            latestNewsContainer.appendChild(newsItem);
        });

        // Populate Events & Downloads
        const eventsContainer = document.getElementById("events");
        eventsContainer.innerHTML = "";
        data.events.forEach(event => {
            const eventItem = document.createElement("div");
            eventItem.innerHTML = `
                <p><strong>${event.title}</strong></p>
                <p>${event.date}</p>
                <a href="${event.link}">More details</a>
            `;
            eventsContainer.appendChild(eventItem);
        });

        // Show the modal
        document.getElementById("company-details-modal").style.display = "block";

        // Prepare data for the chart
        if (data.price_history?.data) {
            // Sort the price history by date in ascending order
            const sortedData = data.price_history.data.sort((a, b) => new Date(a.date) - new Date(b.date));

            // Extract labels (dates) and prices
            const labels = sortedData.map(item => item.date);
            const prices = sortedData.map(item => item.price);

            console.log("Sorted Chart Labels:", labels);
            console.log("Sorted Chart Prices:", prices);

            // Destroy previous chart instance if it exists
            const ctx = document.getElementById("share-price-chart").getContext("2d");

if (window.chartInstance) {
    window.chartInstance.destroy();
}

window.chartInstance = new Chart(ctx, {
  type: 'line',
  data: {
    labels: labels,  // x-axis: dates
    datasets: [{
      label: 'Share Price',
      data: prices,
      borderColor: 'blue',
      backgroundColor: 'transparent',
      borderWidth: 2,
      tension: 0.4,         // Smooth curve
      pointRadius: 0,       // Hide points
      pointHoverRadius: 5   // Show dot on hover
    }]
  },
  options: {
    responsive: true,
    interaction: {
      mode: 'index',
      intersect: false
    },
    plugins: {
      tooltip: {
        enabled: true,
        callbacks: {
          label: function(context) {
            return `Price: E${context.parsed.y}`;
          }
        }
      },
      legend: {
        display: false
      }
    },
    scales: {
      x: {
        title: {
          display: true,
          text: 'Date'
        },
        ticks: {
          autoSkip: true,
          maxTicksLimit: 6,
          maxRotation: 45,
          minRotation: 30
        },
        grid: {
          display: true,
          color: '#e0e0e0'
        }
      },
      y: {
        beginAtZero: true,
        title: {
          display: true,
          text: 'Price (E)'
        },
        grid: {
          display: true,
          color: '#e0e0e0'
        }
      }
    }
  }
});




        }
    } catch (error) {
        console.error("Error fetching company details:", error);
    }
}

// Function to close the modal
function closeCompanyDetails() {
    document.getElementById("company-details-modal").style.display = "none";
}


