let pollo = 0, pizza = 0;

const polloEl = document.getElementById("polloPts");
const pizzaEl = document.getElementById("pizzaPts");
const barPollo = document.getElementById("barPollo");
const barPizza = document.getElementById("barPizza");
const winner = document.getElementById("winnerText");

document.getElementById("addPollo").addEventListener("click", ()=>{
    pollo++; actualizar();
});
document.getElementById("addPizza").addEventListener("click", ()=>{
    pizza++; actualizar();
});
document.getElementById("resetBtn").addEventListener("click", ()=>{
    pollo = 0; pizza = 0; actualizar();
});

function actualizar(){
    polloEl.textContent = pollo;
    pizzaEl.textContent = pizza;

    const total = pollo + pizza || 1;
    barPollo.style.width = (pollo/total)*100 + "%";
    barPizza.style.width = (pizza/total)*100 + "%";

    barPollo.textContent = pollo + " pts";
    barPizza.textContent = pizza + " pts";

    if(pollo > pizza){
        winner.textContent = "¡POLLO VA GANANDO!";
        winner.style.color = "#FFD700";
    } else if (pizza > pollo){
        winner.textContent = "¡PIZZA VA GANANDO!";
        winner.style.color = "#FFA500";
    } else {
        winner.textContent = "¡EMPATE!";
        winner.style.color = "#0af";
    }
}
