// index.js
document.addEventListener('DOMContentLoaded', function () {
    updateTables();
    setInterval(updateTables, 5000);
});

function updateTables() {
    fetch('/monitor')
        .then(response => response.json())
        .then(data => {
            document.querySelector('.table.getData').innerHTML = generateTableHtml(data.getData);
            document.querySelector('.table.accountSummary').innerHTML = generateTableHtml(data.accountSummary);
            document.querySelector('.table.liveTrading').innerHTML = generateTableHtml(data.liveTrading);
        });
}

function generateTableHtml(data) {
    let html = '<tr>';
    for (let key in data) {
        html += `<th>${key}</th>`;
    }
    html += '</tr>';
    html += '<tr>';
    for (let key in data) {
        html += `<td>${data[key]}</td>`;
    }
    html += '</tr>';
    return html;
}


// function generateTableHtml(data) {
//     let html = '<tr>';
//     for (let key in data) {
//         html += `<th>${key}</th>`;
//     }
//     html += '</tr>';
//     html += '<tr>';
//     for (let key in data) {
//         // Check if the value is a number, if so, format it
//         if (!isNaN(data[key]) && !isNaN(parseFloat(data[key]))) {
//             let formattedNumber = parseFloat(data[key]).toLocaleString('en', {minimumFractionDigits: 2, maximumFractionDigits: 2});
//             html += `<td>${formattedNumber}</td>`;
//         } else {
//             html += `<td>${data[key]}</td>`;
//         }
//     }
//     html += '</tr>';
//     return html;
// }