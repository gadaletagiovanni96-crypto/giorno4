document.addEventListener("DOMContentLoaded", () => {
    // --- GESTIONE DELLO SLIDER (PAGINE) ---
    const slides = document.querySelectorAll('.slide');
    const prevBtn = document.getElementById('prevBtn');
    const nextBtn = document.getElementById('nextBtn');
    const dotsContainer = document.getElementById('dotsContainer');
    
    let currentIndex = 0;
    let startX = 0;
    let endX = 0;

    // Crea i pallini indicatori in base al numero di slide
    slides.forEach((_, index) => {
        const dot = document.createElement('div');
        dot.classList.add('dot');
        if (index === 0) dot.classList.add('active');
        dotsContainer.appendChild(dot);
    });
    
    const dots = document.querySelectorAll('.dot');

    function updateSlider() {
        slides.forEach((slide, index) => {
            slide.classList.remove('active', 'prev');
            if (index === currentIndex) {
                slide.classList.add('active');
            } else if (index < currentIndex) {
                slide.classList.add('prev');
            }
        });

        // Aggiorna i pallini
        dots.forEach((dot, index) => {
            dot.classList.toggle('active', index === currentIndex);
        });

        // Abilita/Disabilita bottoni
        prevBtn.disabled = currentIndex === 0;
        nextBtn.disabled = currentIndex === slides.length - 1;
    }

    // Eventi Bottoni navigazione
    prevBtn.addEventListener('click', () => {
        if (currentIndex > 0) {
            currentIndex--;
            updateSlider();
        }
    });

    nextBtn.addEventListener('click', () => {
        if (currentIndex < slides.length - 1) {
            currentIndex++;
            updateSlider();
        }
    });

    // Gestione Swipe (Scorrimento Touch per Smartphone)
    const sliderContainer = document.querySelector('.slider-container');

    sliderContainer.addEventListener('touchstart', (e) => {
        startX = e.touches[0].clientX;
    });

    sliderContainer.addEventListener('touchend', (e) => {
        endX = e.changedTouches[0].clientX;
        handleSwipe();
    });

    function handleSwipe() {
        const swipeThreshold = 50; // Minima distanza per considerare valido lo swipe
        if (startX - endX > swipeThreshold) {
            // Swipe verso sinistra (Avanti)
            if (currentIndex < slides.length - 1) {
                currentIndex++;
                updateSlider();
            }
        } else if (endX - startX > swipeThreshold) {
            // Swipe verso destra (Indietro)
            if (currentIndex > 0) {
                currentIndex--;
                updateSlider();
            }
        }
    }

    // Inizializza la prima slide
    updateSlider();

    // --- GESTIONE GENERAZIONE PDF ELEGANTE ---
    const downloadPdfBtn = document.getElementById('downloadPdfBtn');
    
    if (downloadPdfBtn) {
        downloadPdfBtn.addEventListener('click', () => {
            // Inizializza jsPDF
            const { jsPDF } = window.jspdf;
            const doc = new jsPDF();
            
            // Colori personalizzati per il PDF (in formato RGB)
            const colorePrincipale = [36, 41, 51]; // Grigio scuro per i titoli
            const coloreAccento = [96, 165, 250];  // Azzurro per le linee decorative
            const coloreTesto = [60, 60, 60];      // Grigio morbido per la lettura
            
            // Variabile per tracciare la posizione verticale (Y) sul foglio
            let yPos = 25;
            const altezzaPagina = doc.internal.pageSize.height;

            // Funzione per cambiare pagina automaticamente se finisce lo spazio
            const controllaSpazio = (spazioRichiesto) => {
                if (yPos + spazioRichiesto >= altezzaPagina - 20) {
                    doc.addPage();
                    yPos = 25; // Resetta la Y in cima alla nuova pagina
                }
            };

            // --- INTESTAZIONE DEL DOCUMENTO ---
            doc.setFont("helvetica", "bold");
            doc.setFontSize(22);
            doc.setTextColor(colorePrincipale[0], colorePrincipale[1], colorePrincipale[2]);
            // Centra il titolo principale
            doc.text("La Luce nel Buio", 105, yPos, { align: "center" });
            
            yPos += 8;
            doc.setFontSize(12);
            doc.setFont("helvetica", "italic");
            doc.setTextColor(100, 100, 100);
            doc.text("Il mio percorso di riflessione", 105, yPos, { align: "center" });
            
            // Linea decorativa
            yPos += 10;
            doc.setDrawColor(coloreAccento[0], coloreAccento[1], coloreAccento[2]);
            doc.setLineWidth(0.5);
            doc.line(20, yPos, 190, yPos); 
            yPos += 15;

            // --- RACCOLTA DELLE RISPOSTE (Ora include tutte e 5 le aree) ---
            const riflessioni = [
                {
                    titolo: "L'illusione della perfezione e la mia maschera:",
                    testo: document.getElementById('riflessione1').value
                },
                {
                    titolo: "Cosa mi ha colpito del video:",
                    testo: document.getElementById('riflessione5').value // Inserito il nuovo riquadro del video
                },
                {
                    titolo: "Le mie crepe e le mie sconfitte:",
                    testo: document.getElementById('riflessione2').value
                },
                {
                    titolo: "Pensieri sulla canzone ascoltata:",
                    testo: document.getElementById('riflessione3').value
                },
                {
                    titolo: "Il mio momento di buio assoluto:",
                    testo: document.getElementById('riflessione4').value
                }
            ];

            // --- STAMPA DELLE SEZIONI NEL PDF ---
            riflessioni.forEach(sezione => {
                controllaSpazio(20); // Controlla se c'è spazio per il titolo
                
                // Stile del titolo della domanda
                doc.setFont("helvetica", "bold");
                doc.setFontSize(14);
                doc.setTextColor(colorePrincipale[0], colorePrincipale[1], colorePrincipale[2]);
                doc.text(sezione.titolo, 20, yPos);
                yPos += 8;
                
                // Stile della risposta del ragazzo
                doc.setFont("helvetica", "normal");
                doc.setFontSize(12);
                doc.setTextColor(coloreTesto[0], coloreTesto[1], coloreTesto[2]);
                
                // Se non ha scritto nulla, metti un testo predefinito
                const contenuto = sezione.testo.trim() !== "" ? sezione.testo : "(Nessun pensiero scritto in questa fase)";
                
                // Divide il testo in righe per non farlo uscire dal foglio (larghezza max 170)
                const righeTesto = doc.splitTextToSize(contenuto, 170); 
                
                controllaSpazio(righeTesto.length * 7); // Controlla lo spazio necessario per le righe
                
                // Scrive il testo riga per riga
                doc.text(righeTesto, 20, yPos);
                
                // Aggiorna la posizione Y per la domanda successiva
                yPos += (righeTesto.length * 6) + 15; 
            });

            // --- SALVATAGGIO DEL FILE ---
            doc.save("Le_Mie_Riflessioni.pdf");
            
            // Feedback visivo sul bottone (diventa verde)
            downloadPdfBtn.innerText = "PDF Salvato! ✔";
            downloadPdfBtn.style.backgroundColor = "#22c55e"; 
            downloadPdfBtn.style.color = "#ffffff";
        });
    }
});