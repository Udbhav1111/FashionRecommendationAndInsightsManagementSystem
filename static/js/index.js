async function addToCart(itemId, itemName, itemImage, itemPrice) {
    try {
        let response = await fetch('/cart', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                image_id: itemId,
                image_url: itemImage,
                quantity: 1,
                price: itemPrice
            })
        });
        if (response.ok) {
            updateCartModal();
        } else {
            console.error('Failed to add item to cart');
        }
    } catch (error) {
        console.error('Error:', error);
    }
}

async function updateCartModal() {
    try {
        let response = await fetch('/cart');
        if (!response.ok) {
            throw new Error('Failed to fetch cart items');
        }
        let cart = await response.json();
        let cartItemsContainer = document.getElementById('cart-items');
        let cartCount = document.getElementById('cart-count');
        let checkoutBtn = document.getElementById('checkout-btn');
        let cartTotal = document.getElementById('cart-total');

        cartItemsContainer.innerHTML = '';
        let totalPrice = 0;

        if (cart.length === 0) {
            cartItemsContainer.innerHTML = '<p class="text-center text-muted">Your cart is empty.</p>';
            checkoutBtn.disabled = true;
            cartCount.innerText = 0;
            cartTotal.innerText = "Total: ₹0.00";
            return;
        }

        cartCount.innerText = cart.length;
        checkoutBtn.disabled = false;

        cart.forEach(item => {
            totalPrice += item.price * item.quantity;
            cartItemsContainer.innerHTML += `
                <li class="list-group-item d-flex justify-content-between align-items-center">
                    <div class="d-flex align-items-center">
                        <img src="${item.image_url}" width="50" height="50" class="rounded me-2">
                        <span>Style - ${item.image_id}</span>
                    </div>
                    <div class="d-flex align-items-center">
                        <button class="btn btn-sm btn-outline-secondary" onclick="updateQuantity(${item.id}, ${item.quantity - 1})">-</button>
                        <span class="mx-2">${item.quantity}</span>
                        <button class="btn btn-sm btn-outline-secondary" onclick="updateQuantity(${item.id}, ${item.quantity + 1})">+</button>
                    </div>
                    <button class="btn btn-danger btn-sm ms-2" onclick="removeFromCart(${item.id})">🗑</button>
                </li>
            `;
        });
        
        cartTotal.innerText = `Total: ₹${totalPrice.toFixed(2)}`;
    } catch (error) {
        console.error('Error:', error);
    }
}

async function updateQuantity(itemId, newQuantity) {
    if (newQuantity < 1) {
        removeFromCart(itemId);
        return;
    }

    try {
        let response = await fetch(`/cart/${itemId}`, {
            method: 'PUT',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ quantity: newQuantity })
        });
        if (response.ok) {
            updateCartModal();
        } else {
            console.error('Failed to update cart item quantity');
        }
    } catch (error) {
        console.error('Error:', error);
    }
}

async function removeFromCart(itemId) {
    try {
        let response = await fetch(`/cart/${itemId}`, {
            method: 'DELETE'
        });
        if (response.ok) {
            updateCartModal();
        } else {
            console.error('Failed to remove item from cart');
        }
    } catch (error) {
        console.error('Error:', error);
    }
}

document.addEventListener("DOMContentLoaded", updateCartModal);

async function goToCheckout() {
    try {
        let response = await fetch('/cart');  // Fetch cart data from API
        let cart = await response.json();  // Parse JSON response

        if (!cart || cart.length === 0) {
            alert("Your cart is empty!");
            return;
        }

        window.location.href = "/checkout";  // Redirect to checkout page
    } catch (error) {
        console.error("Error fetching cart:", error);
        alert("Failed to retrieve cart items. Please try again.");
    }
}

function logoutUser() {
    fetch('/api/logout', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json'
      }
    })
    .then(response => response.json())
    .then(data => {
      alert(data.message); // Show success message
      window.location.href = "/"; // Redirect to home page
    })
    .catch(error => console.error('Error:', error));
  }