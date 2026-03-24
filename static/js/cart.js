const CART_KEY = "olivalle-cart";

function getCart() {
    return JSON.parse(localStorage.getItem(CART_KEY) || "[]");
}

function saveCart(cart) {
    localStorage.setItem(CART_KEY, JSON.stringify(cart));
    updateCartCount();
}

function addToCart(id, name, price) {
    const cart = getCart();
    const existing = cart.find((item) => item.produkt_id === id);
    if (existing) {
        existing.menge += 1;
    } else {
        cart.push({ produkt_id: id, name: name, preis: price, menge: 1 });
    }
    saveCart(cart);
}

function removeFromCart(id) {
    const cart = getCart().filter((item) => item.produkt_id !== id);
    saveCart(cart);
    if (typeof renderCart === "function") renderCart();
}

function updateMenge(id, menge) {
    const cart = getCart();
    const item = cart.find((item) => item.produkt_id === id);
    if (item) {
        item.menge = Math.max(1, menge);
    }
    saveCart(cart);
    if (typeof renderCart === "function") renderCart();
}

function updateCartCount() {
    const cart = getCart();
    const count = cart.reduce((sum, item) => sum + item.menge, 0);
    const el = document.getElementById("cart-count");
    if (el) el.textContent = count;
}

function getCartTotal() {
    return getCart().reduce((sum, item) => sum + item.preis * item.menge, 0);
}

function getVersandkosten(total) {
    return total >= 100 ? 0 : 9.90;
}

document.addEventListener("DOMContentLoaded", updateCartCount);
