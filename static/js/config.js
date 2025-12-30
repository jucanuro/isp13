// Configuración de Temas y Animaciones de Tailwind
tailwind.config = {
    theme: {
        extend: {
            colors: {
                emerald: { 
                    50: '#ecfdf5', 100: '#d1fae5', 200: '#a7f3d0', 300: '#6ee7b7', 
                    400: '#34d399', 500: '#10b981', 600: '#059669', 700: '#047857', 
                    800: '#065f46', 900: '#064e3b', 950: '#022c22'
                },
                accent: '#FBB03B',
            },
            fontFamily: {
                sans: ['Plus Jakarta Sans', 'sans-serif'],
                serif: ['Playfair Display', 'serif'],
            },
            animation: {
                'float': 'float 6s ease-in-out infinite',
            },
            keyframes: {
                float: {
                    '0%, 100%': { transform: 'translateY(0)' },
                    '50%': { transform: 'translateY(-20px)' },
                }
            }
        }
    }
}

document.addEventListener('DOMContentLoaded', () => {
    // RECUERDA: Asegúrate que los nombres coincidan exactamente con tu servidor (con o sin espacios)
    const pdfPaths = {
        'reglamento': '/media/documentos/REGLAMENTO_INTITUCIONAL_2023_2027.pdf',
        'pci': '/media/documentos/PROYECTO_CURRICULAR_INSTITUCIONAL_2023_2027.pdf',
        'manual': '/media/documentos/MANUAL_DE_PROCESOS_INSTITUCIONALES_2023_2027.pdf'
    };

    const modalHTML = `
        <div id="pdf-modal" class="fixed inset-0 z-[999] invisible opacity-0 transition-all duration-500 flex items-center justify-center p-4 lg:p-8">
            <div class="absolute inset-0 bg-slate-950/60 backdrop-blur-md"></div>
            
            <div class="modal-container relative bg-white w-full max-w-5xl h-[95vh] rounded-2xl shadow-[0_0_100px_rgba(0,0,0,0.5)] overflow-hidden flex flex-col transform scale-95 transition-transform duration-500">
                
                <div class="relative z-10 bg-white border-b border-slate-100 px-6 py-4 flex justify-between items-center shadow-sm">
                    <div class="flex items-center gap-4">
                        <div class="w-10 h-10 bg-emerald-50 rounded-xl flex items-center justify-center">
                            <i class="fas fa-file-pdf text-emerald-600 text-lg"></i>
                        </div>
                        <div>
                            <h3 id="modal-title" class="text-sm font-black text-slate-800 uppercase tracking-widest leading-none">Visualizador</h3>
                            <p class="text-[10px] text-emerald-600 font-bold uppercase mt-1 tracking-tighter">Documento Oficial ISEP 13 DE JULIO</p>
                        </div>
                    </div>
                    
                    <div class="flex items-center gap-3">
                        <button id="close-modal" class="group flex items-center gap-2 px-4 py-2 bg-slate-50 hover:bg-red-50 text-slate-400 hover:text-red-600 rounded-xl transition-all duration-300">
                            <span class="text-[10px] font-black uppercase tracking-widest">Cerrar Esc</span>
                            <i class="fas fa-times text-xs"></i>
                        </button>
                    </div>
                </div>

                <div class="flex-grow bg-slate-100 relative overflow-hidden">
                    <div id="pdf-loader" class="absolute inset-0 flex flex-col items-center justify-center bg-white z-0">
                        <div class="w-12 h-12 border-4 border-emerald-200 border-t-emerald-600 rounded-full animate-spin"></div>
                        <p class="mt-4 text-[10px] font-black text-slate-400 uppercase tracking-widest">Cargando Documento...</p>
                    </div>
                    <iframe id="pdf-viewer" src="" class="relative z-10 w-full h-full border-none shadow-inner" style="background: transparent;"></iframe>
                </div>

                <div class="bg-slate-50 px-6 py-3 flex justify-between items-center border-t border-slate-100">
                    <p class="text-[9px] font-medium text-slate-400">© 2025 ISEP 13 DE JULIO - San Pablo, Cajamarca</p>
                    <div class="flex gap-4">
                         <i class="fas fa-shield-halved text-emerald-600/30 text-sm"></i>
                    </div>
                </div>
            </div>
        </div>

        <style>
            #pdf-modal.active {
                visibility: visible;
                opacity: 1;
            }
            #pdf-modal.active .modal-container {
                transform: scale(1);
            }
            /* Personalización del visualizador de PDF */
            #pdf-viewer::-webkit-scrollbar {
                width: 8px;
            }
            #pdf-viewer::-webkit-scrollbar-thumb {
                background: #10b981;
                border-radius: 10px;
            }
        </style>
    `;
    
    document.body.insertAdjacentHTML('beforeend', modalHTML);

    const modal = document.getElementById('pdf-modal');
    const container = modal.querySelector('.modal-container');
    const viewer = document.getElementById('pdf-viewer');
    const closeBtn = document.getElementById('close-modal');
    const links = document.querySelectorAll('.pdf-link');

    links.forEach(link => {
        link.addEventListener('click', (e) => {
            e.preventDefault();
            const pdfKey = link.getAttribute('data-pdf');
            const titleElement = link.querySelector('p');
            const title = titleElement ? titleElement.innerText : "Documento Institucional";
            
            document.getElementById('modal-title').innerText = title;
            
            // Mostrar loader antes de cargar
            document.getElementById('pdf-loader').style.display = 'flex';
            
            viewer.src = pdfPaths[pdfKey];
            modal.classList.add('active');
            document.body.style.overflow = 'hidden';
        });
    });

    // Función cerrar
    const closeModal = () => {
        modal.classList.remove('active');
        setTimeout(() => {
            viewer.src = "";
            document.body.style.overflow = 'auto';
        }, 500);
    };

    closeBtn.addEventListener('click', closeModal);

    // Cerrar con tecla ESC
    document.addEventListener('keydown', (e) => {
        if (e.key === 'Escape' && modal.classList.contains('active')) closeModal();
    });

    // Cerrar al hacer clic fuera (en el desenfoque)
    modal.addEventListener('click', (e) => {
        if (e.target.id === 'pdf-modal') closeModal();
    });
});