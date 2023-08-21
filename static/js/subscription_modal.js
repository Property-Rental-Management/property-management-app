document.addEventListener("DOMContentLoaded", function () {
    const subscriptionPlanSelect = document.getElementById("subscription_plan");
    const periodSelect = document.getElementById("period");
    const totalAmountDisplay = document.getElementById("total_amount_display");
    const subscribeButton = document.getElementById("subscribe_button");

    // Function to enable or disable the subscribe button
    function enableSubscribeButton() {
        subscribeButton.disabled = false;
    }

    function disableSubscribeButton() {
        subscribeButton.disabled = true;
    }

    // Calculate and update the total amount based on selected values
    function updateTotalAmount() {
        const selectedPlanId = subscriptionPlanSelect.value;
        const selectedPeriod = parseInt(periodSelect.value);

        getPlanPrice(selectedPlanId)
            .then(planDetails => {
                if (planDetails !== undefined) {
                    const planPrice = planDetails.price;
                    console.log("plan details : " + planDetails);
                    console.log("plan price : " + planPrice);
                    const totalAmount = planPrice * selectedPeriod;
                    totalAmountDisplay.textContent = `R ${totalAmount.toFixed(2)}`;
                    enableSubscribeButton(); // Enable the button when price is set
                } else {
                    totalAmountDisplay.textContent = "-";
                    disableSubscribeButton(); // Disable the button if no price is set
                    alert("Update your profile before you can subscribe");
                }
            })
            .catch(error => {
                console.error("Error fetching plan details:", error);
                totalAmountDisplay.textContent = "-";
            });
    }

    // Event listeners to update total amount when selections change
    subscriptionPlanSelect.addEventListener("change", updateTotalAmount);
    periodSelect.addEventListener("change", updateTotalAmount);

    // Function to fetch plan details
    async function getPlanPrice(plan_id) {
        const request_url = "/dashboard/plan-data/json/" + plan_id;
        try {
            const response = await fetch(request_url);
            if (!response.ok) {
                throw new Error("Request failed with status: " + response.status);
            }
            const planDetails = await response.json();
            return planDetails;
        } catch (error) {
            console.error("Error fetching plan details:", error);
            return undefined;
        }
    }

    disableSubscribeButton();
});
