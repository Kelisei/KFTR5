function activateModal() {
  document.querySelectorAll(".comment").forEach(function (element) {
    element.addEventListener("click", function (event) {
      let answered_post = event.currentTarget.closest("button").value;
      document.getElementById("answered-post-id").value = answered_post;
      let modal = document.getElementById("modal");
      modal.classList.toggle("hidden");
    });
  });
}
