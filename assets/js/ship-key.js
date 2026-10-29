// ship-key.js
// Reveals and wires the (i) that opens the ship key (#1440).
//
// The button ships `hidden` because the box is a <dialog> opened with
// `showModal`; a browser without it keeps the button hidden. Escape and the
// box's × close it natively. The dialog has no padding and its contents fill
// it, so a click whose target is the dialog itself is on the backdrop and
// closes it too.
(function () {
  var dialog = document.getElementById('ship-key');
  if (!dialog || typeof dialog.showModal !== 'function') return;

  document.querySelectorAll('.ship-key-open').forEach(function (btn) {
    btn.hidden = false;
    btn.addEventListener('click', function () {
      dialog.showModal();
    });
  });

  dialog.addEventListener('click', function (e) {
    if (e.target === dialog) dialog.close();
  });
})();
