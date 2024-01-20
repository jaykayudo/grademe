console.log("Hola.. Welcome to GradeMe.") // Welcome to GradeMe.. created by JAYKAYUDO
const dropTriggers = document.getElementsByClassName('drop-trigger'); // drowdown button for the sidebar
for( let x of dropTriggers){
    x.addEventListener("click", function(e){
    // Event listener for the a side bar drop down button
        let target = e.currentTarget;
        if(target.dataset['target'] != "undefined"){
            let mainTarget = document.querySelector(`${target.dataset['target']}`) // Selecting the element in the data-target attribute
            mainTarget.classList.toggle("nav-show")
            target.classList.toggle("active")
        }
    })  
}

const sideNavTogglers = document.getElementsByClassName('side-nav-toggle'); // Navbar toggle for mobile view
for (let y of sideNavTogglers){
    y.addEventListener("click", function(e){
        let target = e.currentTarget;
        
        let mainTarget = document.querySelector(`.side-nav`)
        mainTarget.classList.toggle("responsive");
        mainTarget.addEventListener("blur", function(e){
            let t = e.currentTarget;
            t.classList.remove("responsive");
        })
            
    })  
}
try{
  const flashMesssageCloseButtons = document.getElementsByClassName("flash-message-close")
    for (let btn of flashMesssageCloseButtons){
        btn.addEventListener('click', function(e){
            let target = e.currentTarget;
            target.closest('.flash-message').classList.add("hidden");
        })
    }  
}catch(e){
    console.log("No messages yet")
}
