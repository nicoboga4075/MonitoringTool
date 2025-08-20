function addEndpoint() {
    const documentContainer = document.getElementById("form-container");
    if (documentContainer.style.display === "none") {
        documentContainer.style.display = "flex";
    } else {
        documentContainer.style.display = "none";
    } 
}

document.addEventListener("DOMContentLoaded", function () {
    const documentContainer = document.getElementById("form-container");
    if (documentContainer != null) {
        documentContainer.addEventListener("submit", function () {
            fetch(`/api/endpoints/${id}`, {
                method: "POST"
            });
        });
    }
});

function handleCheck(id) {
    fetch(`/api/endpoints/${id}/check`, {
        method: "GET"
    })
    .then(response => response.json())
    .then(data => {
        alert(`Response time : ${data.response_time}`);
        location.reload();
    })
}

function handleDelete(id) {
    fetch(`/api/endpoints/${id}`, {
        method: "DELETE"
    }).then(response => {
        if (response.status === 204) {
            location.reload();
        }
    })
}

function handleHistory(id) {
    window.location.href = `/api/endpoints/${id}/history`;
}
