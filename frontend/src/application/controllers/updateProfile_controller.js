// import { Controller } from "@hotwired/stimulus";


// export default class extends Controller {
//     static targets = ["submit"];

//     connect() {
//         console.log("CONNECTING update profile CONTROLLER....");
//     }

//     exit() {
//         // when this is called, I need to get the update form off the page by returning the link template
//         console.log("I MADE IT");
//         fetch(
//             'http://localhost:5000/profile/dissapear',
//             {
//                 method: 'GET',
//             }
//         ).then(
//             response => {
//                 return response;
//             }
//         );
//         // this.submitTarget.click();
//     }
// }