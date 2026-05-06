/**
 * Quiz Timer for QuizCraft
 * Counts down from specified seconds and auto-submits when time expires
 */

function startTimer(seconds, display, form) {
    let timer = seconds;
    let minutes, secs;

    const interval = setInterval(function () {
        minutes = parseInt(timer / 60, 10);
        secs = parseInt(timer % 60, 10);

        minutes = minutes < 10 ? "0" + minutes : minutes;
        secs = secs < 10 ? "0" + secs : secs;

        display.textContent = minutes + ":" + secs;

        // Warning at 1 minute
        if (timer === 60) {
            const card = display.closest('.card');
            if (card) {
                card.classList.remove('bg-warning');
                card.classList.add('bg-danger', 'text-white');
            }
        }

        if (--timer < 0) {
            clearInterval(interval);
            display.textContent = "Time's Up!";
            if (form) {
                alert("Time's up! Submitting your quiz now...");
                form.submit();
            }
        }
    }, 1000);
}

// Auto-scroll to top when quiz starts
window.addEventListener('load', function() {
    window.scrollTo(0, 0);
});
