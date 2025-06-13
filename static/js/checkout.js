document.addEventListener("DOMContentLoaded", function () {
    const checkoutForm = document.getElementById("checkout-form");

    checkoutForm.addEventListener("submit", function (event) {
        event.preventDefault(); // Prevent page reload

        const shippingAddress = document.getElementById("shipping-address").value;
        const paymentMethod = document.querySelector('input[name="payment-method"]:checked').value;
        const userId = 1; // Replace with actual user ID from session

        if (!shippingAddress) {
            alert("Please enter your shipping address.");
            return;
        }

        let cartItems = [];
        document.querySelectorAll(".cart-item").forEach((item) => {
            const imageIdText = item.getAttribute("data-image-id");
            
            const imageId = parseInt(imageIdText.match(/\d+/)[0]);
            const quantity = parseInt(item.querySelector(".quantity").innerText.split(": ")[1]);
            const price = parseFloat(item.querySelector(".total-price").innerText.split(": ₹")[1]);
            console.log(price)
            cartItems.push({
                image_id: imageId,
                quantity: quantity,
                price: price
            });
        });

        if (cartItems.length === 0) {
            alert("Your cart is empty!");
            return;
        }

        const orderData = {
            user_id: userId,
            cart_items: cartItems,
            payment_method: paymentMethod,
            shipping_address: shippingAddress
        };

        fetch("/checkout", {
            method: "POST",
            headers: {
                "Content-Type": "application/json",
            },
            body: JSON.stringify(orderData),
        })
        .then(response => response.json())
        .then(data => {
            if (data.order_id) {
                alert("Order placed successfully! Redirecting to My Orders...");
                window.location.href = "/orders"; // Redirect to Orders page
            } else {
                alert("Error placing order: " + data.error);
            }
        })
        .catch(error => {
            console.error("Error:", error);
            alert("Something went wrong. Please try again.");
        });
    });
    console.cart
});
