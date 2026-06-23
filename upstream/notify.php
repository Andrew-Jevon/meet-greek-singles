<?php
if ($_SERVER["REQUEST_METHOD"] == "POST") {
    // 1. Sanitize and collect input
    $name  = filter_input(INPUT_POST, 'name', FILTER_SANITIZE_SPECIAL_CHARS);
    $email = filter_input(INPUT_POST, 'email', FILTER_VALIDATE_EMAIL);

    // 2. Configuration
    $to      = "azadv0174@gmail.com"; // <-- Change this to your email
    $subject = "New Launch Notification Sign-up";
    
    // 3. Validation
    if (!$email) {
        echo "Invalid email address.";
        exit;
    }

    // 4. Construct Email Body
    $message = "You have a new subscriber!\n\n";
    $message .= "Name: " . $name . "\n";
    $message .= "Email: " . $email . "\n";

    // 2026-04-25: was support@meetgreeksingles.com — that mailbox doesn't
    // exist on the GoDaddy host; bounced. info@ is the configured account.
    $headers = "From: info@meetgreeksingles.com\r\n";
    $headers .= "Reply-To: " . $email . "\r\n";

    // 5. Send and Respond
    if (mail($to, $subject, $message, $headers)) {
        // Redirect back or show success
        echo "Success! Thank you for signing up.";
    } else {
        echo "Oops! Something went wrong on our end.";
    }
} else {
    // Prevent direct access to the script
    header("Location: index.html");
    exit;
}
?>