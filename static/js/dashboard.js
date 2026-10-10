(function () {
  const edit = document.getElementById("editProfile");
  const form = document.getElementById("profileForm");
  if (edit && form) {
    edit.addEventListener("click", () => {
      form.hidden = !form.hidden;
      edit.textContent = form.hidden ? "Edit profile" : "Hide editor";
    });
  }
  const add = document.getElementById("addProject");
  const pform = document.getElementById("portfolioForm");
  if (add && pform) {
    add.addEventListener("click", () => {
      pform.hidden = !pform.hidden;
    });
  }
})();
