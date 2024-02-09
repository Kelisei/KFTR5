function activateModal() {
  document.querySelectorAll(".comment").forEach(function (element) {
    element.addEventListener("click", function (event) {
      let answered_post = event.target.closest("button").value;
      document.getElementById("answered-post-id").value = answered_post;
      let modal = document.getElementById("modal");
      if (modal.classList.contains("hidden")) {
        modal.classList.remove("hidden");
      } else {
        modal.classList.add("hidden");
      }
    });
  });
}
