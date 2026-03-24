// Warenkorb-Logik — wird in Task 4 implementiert
function addToCart(id, name, price) {
    console.log("TODO: addToCart", id, name, price);
}

function updateCartCount() {
    const cart = JSON.parse(localStorage.getItem("olivalle-cart") || "[]");
    const count = cart.reduce((sum, item) => sum + item.menge, 0);
    const el = document.getElementById("cart-count");
    if (el) el.textContent = count;
}

document.addEventListener("DOMContentLoaded", updateCartCount);
