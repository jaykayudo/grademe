function loadScript(){
    const emailInput = document.querySelector("#currentEmail")
const formCover = document.querySelector("#forms")
const createEmailElement = (id)=>{
    const emailcover = document.createElement('div');
    const label = document.createElement('label')
    const span = document.createElement('span')
    const input = document.createElement('input')
    emailcover.classList.add("form-group")
    emailcover.appendChild(label)
    label.appendChild(document.createTextNode("New Email"))
    label.classList.add("form-input-label")
    input.classList.add('form-input')
    input.placeholder = "EX: emailaddress@domain.com"
    input.id = id
    input.type="email"
    emailcover.appendChild(input)
    span.classList.add("error-text")
    emailcover.appendChild(span)
    return emailcover
}
const createCodeElement = (labeltext,id)=>{
    const codecover = document.createElement('div');
    const label = document.createElement('label')
    const span = document.createElement('span')
    const span2 = document.createElement('span')

    const input = document.createElement('input')
    codecover.classList.add("form-group")
    codecover.appendChild(label)
    label.appendChild(document.createTextNode(labeltext))
    label.classList.add("form-input-label");
    input.classList.add('form-input')
    input.placeholder = "EX: 012345"
    input.id = id
    input.type="tel"
    input.maxLength=6
    input.pattern="\d*"
    codecover.appendChild(input)
    span.classList.add("error-text")
    codecover.appendChild(span)
    span2.appendChild(document.createTextNode(`A 6 digit code has been sent to your email.`))
    span2.classList.add("small-text")
    codecover.appendChild(span2);
    return codecover
}
let statusDigit = 1;
const submitButton = document.querySelector("#submitBtn");
let verifiedCurrentEmail = false;
let verifiedNewEmail = false;
const validateEmail = (email,errorTag)=>{
    if(email.trim() == ""){
        errorTag.innerHTML = "email field should not be blank"
        return false
    }
    var validRegex = /^[a-zA-Z0-9.!#$%&'*+/=?^_`{|}~-]+@[a-zA-Z0-9-]+(?:\.[a-zA-Z0-9-]+)*$/;
    if (!email.match(validRegex)) {
        errorTag.innerHTML = "email field should contain a valid email"
        return false
    }
    errorTag.innerHTML = ""
    return true
}
const validateCode = (code, errorTag)=>{
    if(code.trim() == ""){
        errorTag.innerHTML = "code field should not be blank"
        return false
    }
    if (isNaN(code)){
        errorTag.innerHTML = "code field should contain only numbers"
        return false
    }
    if(code.length !== 6){
        errorTag.innerHTML = "code should be 6 digits"
        return false
    }
    errorTag.innerHTML = ""
    return true
}
function addToForms(element){
    formCover.appendChild(element);

}
const currentEmailAjax = (emailInput,target)=>{
    $.ajax({
        url:'/change-email/verify-current-email/',
        type:'post',
        data:{
            currentemail: emailInput.value,
            csrfmiddlewaretoken: document.querySelector('[name=csrfmiddlewaretoken]').value,
        },
        success: function(response){
            addToForms(createCodeElement("Current Email Code","currentCode"));
            statusDigit = 2;
            emailInput.disabled = true;
            emailInput.nextElementSibling.innerHTML = "";
            target.innerHTML = "Submit";
            target.disabled = false;
        },
        error: function(response){
            console.log(response)
            emailInput.nextElementSibling.innerHTML = response.responseJSON.message;
            target.innerHTML = "Submit";
            target.disabled = false;
        }
    });
            
}
const currentCodeAjax = (emailInput,codeInput, target)=>{
    $.ajax({
        url:'/change-email/verify-current-email-code/',
        type:'post',
        data:{
            currentemail: emailInput.value,
            currentcode: codeInput.value,
            csrfmiddlewaretoken: document.querySelector('[name=csrfmiddlewaretoken]').value,
        },
        success: function(response){
            addToForms(createEmailElement("newEmail"));
            statusDigit = 3;
            codeInput.disabled = true;
            codeInput.nextElementSibling.innerHTML = "";
            verifiedCurrentEmail = true;
            target.innerHTML = "Submit";
            target.disabled = false;
            
        },
        error: function(response){
            codeInput.nextElementSibling.innerHTML = response.responseJSON.message;
            target.innerHTML = "Submit";
            target.disabled = false;
        }
    });
            
}
const verifyNewEmailAjax = (emailInput,codeInput,newInput,target)=>{
    $.ajax({
        url:'/change-email/verify-new-email/',
        type:'post',
        data:{
            currentemail: emailInput.value,
            currentcode: codeInput.value,
            newemail: newInput.value,
            csrfmiddlewaretoken: document.querySelector('[name=csrfmiddlewaretoken]').value,
        },
        success: function(response){
            addToForms(createCodeElement("New Email Code","newCode"));
            statusDigit = 4;
            newInput.disabled = true;
            newInput.nextElementSibling.innerHTML ="";
            target.innerHTML = "Submit";
            target.disabled = false;
        },
        error: function(response){
            newInput.nextElementSibling.innerHTML = response.responseJSON.message;
            target.innerHTML = "Submit";
            target.disabled = false;
        }
    });
            
}
const fullSubmission = (emailInput,codeInput,newInput,newCodeInput, target)=>{
    $.ajax({
        url:'/change-email/verify-new-email-code/',
        type:'post',
        data:{
            currentemail: emailInput.value,
            currentcode: codeInput.value,
            newemail: newInput.value,
            newcode: newCodeInput.value,
            csrfmiddlewaretoken: document.querySelector('[name=csrfmiddlewaretoken]').value,
        },
        success: function(response){
            newCodeInput.disabled = true;
            newCodeInput.nextElementSibling.innerHTML = "";
            target.innerHTML = "Email Changed Successfully";
            setTimeout(()=>{
                window.location.reload();
            },2000)
        },
        error: function(response){
            newCodeInput.nextElementSibling.innerHTML = response.responseJSON.message;
            target.innerHTML = "Submit";
            target.disabled = false;
        }
    });
            
}
submitButton.addEventListener("click", function(e){
    e.stopImmediatePropagation();
    let target = e.currentTarget;
    ;
    if(statusDigit == 1){
        console.log(emailInput.closest('.form-group').n)
        if(validateEmail(emailInput.value,emailInput.nextElementSibling)){
            target.innerHTML = "Loading...";
            target.disabled = true
            currentEmailAjax(emailInput,target)
        }
        
    }else if(statusDigit == 2){
        let code = document.getElementById("currentCode")
        if(validateCode(code.value, code.nextElementSibling)){
            target.innerHTML = "Loading...";
            target.disabled = true
            
            currentCodeAjax(emailInput,code,target)
        }
        
    }else if(statusDigit == 3){
        let code = document.getElementById("currentCode")
        let newEmail = document.getElementById("newEmail")
        if(validateEmail(newEmail.value, newEmail.nextElementSibling)){
            target.innerHTML = "Loading...";
            target.disabled = true
            verifyNewEmailAjax(emailInput,code,newEmail,target)
        }
        
    }else if(statusDigit == 4){
        let code = document.getElementById("currentCode")
        let newEmail = document.getElementById("newEmail")
        let newCode = document.getElementById("newCode")
        if(validateCode(newCode.value, newCode.nextElementSibling)){
            target.innerHTML = "Loading...";
            target.disabled = true
            fullSubmission(emailInput,code,newEmail,newCode,target)
        }
    
    }  
})
}

window.addEventListener("load",function(){
    loadScript()
})