const CART_KEY = "olivalle-cart";

function getCart() {
    return JSON.parse(localStorage.getItem(CART_KEY) || "[]");
}

function saveCart(cart) {
    localStorage.setItem(CART_KEY, JSON.stringify(cart));
    updateCartCount();
}

function addToCart(id, name, price, buttonEl) {
    const cart = getCart();
    const existing = cart.find((item) => item.produkt_id === id);
    if (existing) {
        existing.menge += 1;
    } else {
        cart.push({ produkt_id: id, name: name, preis: price, menge: 1 });
    }
    saveCart(cart);

    // Button-Animation
    if (buttonEl) {
        const originalText = buttonEl.textContent;
        buttonEl.textContent = "Hinzugefügt ✓";
        buttonEl.classList.remove("bg-accent", "hover:bg-yellow-400");
        buttonEl.classList.add("bg-green-600", "text-white");
        setTimeout(() => {
            buttonEl.textContent = originalText;
            buttonEl.classList.remove("bg-green-600", "text-white");
            buttonEl.classList.add("bg-accent", "hover:bg-yellow-400");
        }, 1000);
    }

    // Flyout anzeigen (wird in Task 4 implementiert)
    if (typeof showCartFlyout === "function") {
        setTimeout(() => showCartFlyout(), 300);
    }
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

function increaseMenge(id) {
    const cart = getCart();
    const item = cart.find((item) => item.produkt_id === id);
    if (item) {
        item.menge += 1;
        saveCart(cart);
        if (typeof renderCart === "function") renderCart();
    }
}

function decreaseMenge(id) {
    const cart = getCart();
    const item = cart.find((item) => item.produkt_id === id);
    if (item) {
        if (item.menge <= 1) {
            removeFromCart(id);
        } else {
            item.menge -= 1;
            saveCart(cart);
            if (typeof renderCart === "function") renderCart();
        }
    }
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
