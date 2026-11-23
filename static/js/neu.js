// Oberfläche des neuen Kunden-Frontends (/neu).
// Der Warenkorb selbst (Speicher, Summen, Versandkosten) kommt unverändert aus
// cart.js — hier wird nur dargestellt. Produktnamen immer per textContent.

(function () {
    "use strict";

    const chf = (n) => "CHF " + n.toFixed(2);
    const $ = (sel, root) => (root || document).querySelector(sel);
    const $$ = (sel, root) => Array.from((root || document).querySelectorAll(sel));

    function anzahl() {
        return getCart().reduce((sum, item) => sum + item.menge, 0);
    }

    // --- Gratisversand-Fortschritt (Schublade + Warenkorbseite) ---
    function zeichneGratis(subtotal) {
        const gratisAb = parseFloat(document.body.dataset.gratisAb);
        const rest = gratisAb - subtotal;
        const text = rest > 0
            ? "Noch " + chf(rest) + " bis zum Gratis-Versand"
            : "Du erhältst Gratis-Versand ✓";
        const prozent = Math.max(0, Math.min(100, (subtotal / gratisAb) * 100));
        $$("[data-neu-gratis-text]").forEach((el) => { el.textContent = text; });
        $$("[data-neu-gratis-balken]").forEach((el) => { el.style.width = prozent + "%"; });
    }

    // --- Schublade ---
    function zeichneSchublade() {
        const cart = getCart();
        const leer = $("#neu-drawer-leer");
        const voll = $("#neu-drawer-voll");
        if (!leer || !voll) return;
        const istLeer = cart.length === 0;
        leer.classList.toggle("hidden", !istLeer);
        leer.classList.toggle("flex", istLeer);
        voll.classList.toggle("hidden", istLeer);
        voll.classList.toggle("flex", !istLeer);
        if (istLeer) return;

        const liste = $("#neu-drawer-items");
        const vorlage = $("#neu-drawer-item");
        liste.innerHTML = "";
        cart.forEach((item) => {
            const zeile = vorlage.content.cloneNode(true);
            const bild = $(".neu-item-bild", zeile);
            bild.src = item.image || "/static/images/products/olivalle-250ml.jpeg";
            bild.alt = item.name;
            $(".neu-item-name", zeile).textContent = item.name;
            $(".neu-item-preis", zeile).textContent = chf(item.preis * item.menge);
            $(".neu-item-menge", zeile).textContent = item.menge;
            $(".neu-item-minus", zeile).addEventListener("click", () => { decreaseMenge(item.produkt_id); aktualisiere(); });
            $(".neu-item-plus", zeile).addEventListener("click", () => { increaseMenge(item.produkt_id); aktualisiere(); });
            $(".neu-item-weg", zeile).addEventListener("click", () => { removeFromCart(item.produkt_id); aktualisiere(); });
            liste.appendChild(zeile);
        });

        const subtotal = getCartTotal();
        const versand = getVersandkosten(subtotal);
        $$("#neu-drawer [data-neu-versand]").forEach((el) => { el.textContent = versand > 0 ? chf(versand) : "gratis"; });
        $$("#neu-drawer [data-neu-total]").forEach((el) => { el.textContent = chf(subtotal + versand); });
    }

    function oeffneSchublade() {
        zeichneSchublade();
        $("#neu-drawer").classList.remove("translate-x-full");
        $("#neu-drawer").classList.add("shadow-2xl");
        $("#neu-drawer").setAttribute("aria-hidden", "false");
        $("#neu-drawer").inert = false;
        $("#neu-drawer-overlay").classList.remove("opacity-0", "pointer-events-none");
        document.body.classList.add("overflow-hidden");
    }

    function schliesseSchublade() {
        $("#neu-drawer").classList.add("translate-x-full");
        $("#neu-drawer").classList.remove("shadow-2xl");
        $("#neu-drawer").setAttribute("aria-hidden", "true");
        $("#neu-drawer").inert = true;
        $("#neu-drawer-overlay").classList.add("opacity-0", "pointer-events-none");
        document.body.classList.remove("overflow-hidden");
    }

    // --- Fixe Leiste auf dem Handy (nicht im Warenkorb / an der Kasse) ---
    function zeichneMobilleiste() {
        const leiste = $("#neu-mobilleiste");
        if (!leiste) return;
        const seite = document.body.dataset.neuSeite;
        const n = anzahl();
        const zeigen = n > 0 && !["warenkorb", "checkout", "bestaetigung"].includes(seite);
        leiste.classList.toggle("hidden", !zeigen);
        leiste.classList.toggle("flex", zeigen);
        $("[data-neu-mobil-text]", leiste).textContent =
            n + " Artikel · " + chf(getCartTotal());
    }

    function aktualisiere() {
        updateCartCount();
        zeichneGratis(getCartTotal());
        zeichneSchublade();
        zeichneMobilleiste();
        if (typeof window.neuSeiteAktualisieren === "function") window.neuSeiteAktualisieren();
    }
    window.neuAktualisiere = aktualisiere;

    // --- Klicks ---
    document.addEventListener("click", (e) => {
        if (e.target.closest("[data-neu-drawer-open]")) { oeffneSchublade(); return; }
        if (e.target.closest("[data-neu-drawer-close]") || e.target.id === "neu-drawer-overlay") {
            schliesseSchublade();
            return;
        }

        // Mengenwahl auf der Produktkarte
        const schritt = e.target.closest("[data-neu-schritt]");
        if (schritt) {
            const feld = $("[data-neu-menge]", schritt.closest("[data-neu-karte]"));
            const neu = Math.max(1, Math.min(99, parseInt(feld.textContent, 10) + parseInt(schritt.dataset.neuSchritt, 10)));
            feld.textContent = neu;
            return;
        }

        // In den Warenkorb (Menge von der Karte)
        const btn = e.target.closest("[data-neu-add]");
        if (btn) {
            const karte = btn.closest("[data-neu-karte]");
            const feld = karte ? $("[data-neu-menge]", karte) : null;
            const menge = feld ? parseInt(feld.textContent, 10) : 1;
            for (let i = 0; i < menge; i++) {
                addToCart(
                    parseInt(btn.dataset.productId, 10),
                    btn.dataset.productName,
                    parseFloat(btn.dataset.productPrice),
                    btn.dataset.productImage,
                    null,
                    btn.dataset.productAktion === "1"
                );
            }
            if (feld) feld.textContent = "1";
            const label = $("[data-neu-add-label]", btn);
            if (label) {
                const vorher = label.textContent;
                label.textContent = "Hinzugefügt ✓";
                setTimeout(() => { label.textContent = vorher; }, 1200);
            }
            aktualisiere();
            oeffneSchublade();
        }
    });

    document.addEventListener("keydown", (e) => {
        if (e.key === "Escape") schliesseSchublade();
    });

    // --- Sanftes Einblenden beim Scrollen ---
    function einblenden() {
        const elemente = $$("[data-neu-reveal]");
        const ruhig = window.matchMedia("(prefers-reduced-motion: reduce)").matches;
        if (ruhig || !("IntersectionObserver" in window)) return;
        elemente.forEach((el) => el.classList.add("opacity-0", "translate-y-4", "transition-all", "duration-700"));
        const beobachter = new IntersectionObserver((eintraege) => {
            eintraege.forEach((eintrag) => {
                if (!eintrag.isIntersecting) return;
                eintrag.target.classList.remove("opacity-0", "translate-y-4");
                beobachter.unobserve(eintrag.target);
            });
        }, { threshold: 0.12 });
        elemente.forEach((el) => beobachter.observe(el));
    }

    document.addEventListener("DOMContentLoaded", () => {
        aktualisiere();
        einblenden();
    });
})();
