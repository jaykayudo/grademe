function resultNeed (){

   $("#add-form").click(function(){
    $("#dynamic-group").append(html);
    }
    )
    $("#dynamic-group").on('click','#remove',function(){
    $(this).closest('.group-container').remove()
    }) 
}

function bulkResultNeed (){
    const fileButton = document.getElementById('file-btn');
    const file = document.getElementById('file')
    fileButton.addEventListener('click', function(){
        file.click();
    })
    file.addEventListener("change",function(e){
        if(e.currentTarget.value != ""){
            fileButton.innerHTML = e.currentTarget.files[0].name;
        }else{
            fileButton.innerHTML = "Choose File";
        }
    })
    
}
function addStudentNeed (){
    const fileButton = document.getElementById('file-btn');
    const file = document.getElementById('file')
    fileButton.addEventListener('click', function(){
        file.click();
    })
    file.addEventListener("change",function(e){
        if(e.currentTarget.value != ""){
            fileButton.innerHTML = e.currentTarget.files[0].name;
        }else{
            fileButton.innerHTML = "Choose File";
        }
    })
}

