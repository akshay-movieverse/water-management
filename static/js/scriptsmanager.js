document.addEventListener('DOMContentLoaded', function () {
    // Function to calculate Amount (₹) and Water Supply
    function calculateValues(subunitId) {
        const openingAmount = parseFloat(document.querySelector(`#closing_amount_${subunitId}`).getAttribute('data-opening-amount')) || 0;
        const openingDispenser = parseFloat(document.querySelector(`#closing_dispenser_${subunitId}`).getAttribute('data-opening-dispenser')) || 0;

        const closingAmount = parseFloat(document.querySelector(`#closing_amount_${subunitId}`).value) || 0;
        const closingDispenser = parseFloat(document.querySelector(`#closing_dispenser_${subunitId}`).value) || 0;

        // Calculate Amount (₹)
        const amountRs = Math.max(closingAmount - openingAmount, 0); // Ensure non-negative
        document.querySelector(`#amount_rs_${subunitId}`).textContent = amountRs.toFixed(2);

        // Calculate Water Supply
        const waterSupply = Math.max(closingDispenser - openingDispenser, 0); // Ensure non-negative
        document.querySelector(`#water_supply_${subunitId}`).textContent = waterSupply.toFixed(2);
    }

    // Function to validate a single input
    function validateInput(input) {
        const openingValue = parseFloat(input.getAttribute(`data-${input.classList.contains('closing-amount') ? 'opening-amount' : 'opening-dispenser'}`));
        const closingValue = parseFloat(input.value) || 0;

        if (input.value.trim() !== '' && closingValue < openingValue) {
            input.classList.add('is-invalid');
            input.nextElementSibling.style.display = 'block'; // Show error message
            return false;
        } else {
            input.classList.remove('is-invalid');
            input.nextElementSibling.style.display = 'none'; // Hide error message
            return true;
        }
    }

    // Function to validate subunit inputs
    function validateSubunit(subunitId) {
        const closingAmount = document.querySelector(`#closing_amount_${subunitId}`);
        const closingDispenser = document.querySelector(`#closing_dispenser_${subunitId}`);
        const card = closingAmount.closest('.card');

        // Check if both fields are filled or both are empty
        const isAmountFilled = closingAmount.value.trim() !== '';
        const isDispenserFilled = closingDispenser.value.trim() !== '';

        if (isAmountFilled !== isDispenserFilled) {
            // if (isAmountFilled) {
            //     closingDispenser.classList.add('is-invalid');
            //     closingDispenser.nextElementSibling.style.display = 'block';
            // } else {
            //     closingAmount.classList.add('is-invalid');
            //     closingAmount.nextElementSibling.style.display = 'block';
            // }
            return false;
        } else {
            // closingAmount.classList.remove('is-invalid');
            // closingDispenser.classList.remove('is-invalid');
            // closingAmount.nextElementSibling.style.display = 'none';
            // closingDispenser.nextElementSibling.style.display = 'none';
            return true;
        }
    }

    // Function to update card shadow based on filled and valid inputs
    function updateCardShadow(subunitId) {
        const closingAmount = document.querySelector(`#closing_amount_${subunitId}`);
        const closingDispenser = document.querySelector(`#closing_dispenser_${subunitId}`);
        const card = closingAmount.closest('.card');

        const isAmountValid = closingAmount.value.trim() !== ''  ? validateInput(closingAmount) : false;
        const isDispenserValid = closingDispenser.value.trim() !== '' ? validateInput(closingDispenser) : false;

        if (closingAmount.value.trim() !== '' && closingDispenser.value.trim() !== '' && isAmountValid && isDispenserValid) {
            card.style.boxShadow = '0 0 0 .25rem rgb(208 0 194 / 38%)';
        } else {
            card.style.boxShadow = '';
        }
    }

    // Attach event listeners to all input fields
    document.querySelectorAll('.closing-amount, .closing-dispenser').forEach(input => {
        input.addEventListener('input', function () {
            const subunitId = this.getAttribute('data-subunit-id');
            calculateValues(subunitId);
            validateInput(this); // Validate the current input
            validateSubunit(subunitId); // Validate the subunit
            updateCardShadow(subunitId); // Update card shadow
        });
    });

    // Initialize calculations and card shadows for all subunits
    document.querySelectorAll('.closing-amount').forEach(input => {
        const subunitId = input.getAttribute('data-subunit-id');
        calculateValues(subunitId);
        updateCardShadow(subunitId);
    });

    // Prevent form submission if there are invalid inputs
    document.querySelector('form').addEventListener('submit', function (event) {
        let isValid = true;
        document.querySelectorAll('.closing-amount, .closing-dispenser').forEach(input => {
            if (!validateInput(input)) {
                isValid = false;
            }
        });

        // Validate all subunits
        document.querySelectorAll('.card').forEach(card => {
            const subunitId = card.querySelector('.closing-amount').getAttribute('data-subunit-id');
            if (!validateSubunit(subunitId)) {
                isValid = false;
            }
        });

        if (!isValid) {
            event.preventDefault();
            alert('Please correct the errors before submitting.');
        }
    });
});