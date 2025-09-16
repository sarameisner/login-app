function toggle_menu(){
    const main_menu = document.querySelector(".main_one")
    console.log(main_menu)
    if(main_menu.classList.contains("active")){
        main_menu.classList.remove("active")
    }else{
        main_menu.classList.add("active")
    }
}