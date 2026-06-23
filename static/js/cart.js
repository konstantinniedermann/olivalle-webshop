const CART_KEY = "olivalle-cart";

function getCart() {
    return JSON.parse(localStorage.getItem(CART_KEY) || "[]");
}

function saveCart(cart) {
    localStorage.setItem(CART_KEY, JSON.stringify(cart));
    updateCartCount();
}

function addToCart(id, name, price, image, buttonEl, aktion) {
    const cart = getCart();
    const existing = cart.find((item) => item.produkt_id === id);
    if (existing) {
        existing.menge += 1;
    } else {
        cart.push({ produkt_id: id, name: name, preis: price, image: image, menge: 1, aktion: !!aktion });
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

    if (typeof showCartFlyout === "function") {
        setTimeout(() => showCartFlyout(), 300);
    }
}

function removeFromCart(id) {
    const cart = getCart().filter((item) => item.produkt_id !== id);
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

function getRabattSubtotal() {
    return getCart().reduce((sum, item) => sum + (item.aktion ? 0 : item.preis * item.menge), 0);
}

function getVersandkosten(total) {
    return total >= 100 ? 0 : 9.90;
}

let flyoutTimer = null;

function showCartFlyout() {
    const flyout = document.getElementById("cart-flyout");
    const itemsContainer = document.getElementById("cart-flyout-items");
    const totalEl = document.getElementById("cart-flyout-total");
    if (!flyout || !itemsContainer || !totalEl) return;

    const cart = getCart();
    if (cart.length === 0) return;

    // Inhalt rendern
    itemsContainer.innerHTML = cart
        .map(
            (item) =>
                `<div class="flex justify-between text-stone-200">
                    <span>${item.menge}\u00d7 ${item.name}</span>
                    <span>CHF ${(item.preis * item.menge).toFixed(2)}</span>
                </div>`
        )
        .join("");
    totalEl.textContent = "CHF " + getCartTotal().toFixed(2);

    // Smooth einblenden
    flyout.classList.remove("opacity-0", "pointer-events-none", "translate-y-1");
    flyout.classList.add("opacity-100", "pointer-events-auto", "translate-y-0");

    // Timer: nach 4s automatisch schliessen
    if (flyoutTimer) clearTimeout(flyoutTimer);
    flyoutTimer = setTimeout(() => hideCartFlyout(), 4000);
}

function hideCartFlyout() {
    const flyout = document.getElementById("cart-flyout");
    if (flyout) {
        flyout.classList.remove("opacity-100", "pointer-events-auto", "translate-y-0");
        flyout.classList.add("opacity-0", "pointer-events-none", "translate-y-1");
    }
    if (flyoutTimer) {
        clearTimeout(flyoutTimer);
        flyoutTimer = null;
    }
}

// Klick ausserhalb schliesst Flyout
document.addEventListener("click", (e) => {
    const flyout = document.getElementById("cart-flyout");
    if (flyout && !flyout.closest(".relative").contains(e.target)) {
        hideCartFlyout();
    }
});

document.addEventListener("DOMContentLoaded", updateCartCount);

// Delegierter Handler für "In den Warenkorb"-Buttons.
// Ersetzt frühere inline onclick-Handler, damit die CSP (script-src ohne
// 'unsafe-inline') Inline-Event-Handler blocken kann.
document.addEventListener("click", (e) => {
    const btn = e.target.closest(".add-to-cart-btn[data-product-id]");
    if (!btn) return;
    addToCart(
        parseInt(btn.dataset.productId, 10),
        btn.dataset.productName,
        parseFloat(btn.dataset.productPrice),
        btn.dataset.productImage,
        btn,
        btn.dataset.productAktion === "1"
    );
});
