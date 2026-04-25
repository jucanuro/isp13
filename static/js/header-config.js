
async function openDynamicModal(modalId) {
    const container = document.getElementById('dynamic-modal-container');
    const contentArea = document.getElementById('dynamic-modal-content');

    if (!container || !contentArea) return;

    document.body.style.overflow = 'hidden';
    container.classList.remove('hidden');
    container.classList.add('flex');
    
    contentArea.innerHTML = `
        <div class="flex flex-col items-center justify-center gap-5 p-20 bg-blue-900/20 backdrop-blur-xl rounded-[3rem] border border-white/10">
            <div class="w-14 h-14 border-4 border-blue-100 border-t-amber-400 rounded-full animate-spin"></div>
            <p class="text-[10px] font-black uppercase tracking-[0.3em] text-white/70">Cargando sección...</p>
        </div>
    `;

    try {
        const modalRoutes = {
            resultados_admision: '/admision/resultados-admision/',
        };

const modalUrl = modalRoutes[modalId] || `/modals/${modalId}/`;

const response = await fetch(modalUrl);
        
        if (!response.ok) throw new Error('No se encontró el contenido');
        
        const html = await response.text();
        
        contentArea.innerHTML = html;

    } catch (error) {
        contentArea.innerHTML = `
            <div class="bg-white p-12 rounded-[3rem] text-center shadow-2xl max-w-sm border border-slate-100">
                <div class="w-16 h-16 bg-rose-50 text-rose-500 rounded-2xl flex items-center justify-center mx-auto mb-6">
                    <i class="fas fa-exclamation-triangle text-2xl"></i>
                </div>
                <h3 class="text-slate-800 font-black uppercase text-sm tracking-tight">Error de conexión</h3>
                <p class="text-slate-500 text-xs mt-3 leading-relaxed">No pudimos cargar la información de "${modalId}". Por favor, intente nuevamente.</p>
                <button onclick="closeDynamicModal()" class="mt-8 w-full py-4 bg-slate-900 text-white rounded-2xl text-[10px] font-black uppercase tracking-widest hover:bg-blue-600 transition-colors">Entendido</button>
            </div>
        `;
    }
}

function closeDynamicModal() {
    const container = document.getElementById('dynamic-modal-container');
    if (container) {
        container.classList.add('hidden');
        container.classList.remove('flex');
    }
    const menuOverlay = document.getElementById('mobile-menu-overlay');
    if (menuOverlay && menuOverlay.classList.contains('invisible')) {
        document.body.style.overflow = 'auto';
    }
}

document.addEventListener('DOMContentLoaded', () => {
    const menuOverlay = document.getElementById('mobile-menu-overlay');
    const menuBackdrop = document.getElementById('mobile-menu-backdrop');
    const menuPanel = document.getElementById('mobile-menu-panel');
    const menuBtn = document.getElementById('btn-mobile-open');
    const closeMenuBtn = document.getElementById('btn-mobile-close');

    window.toggleMenu = function(show) {
        if (!menuOverlay || !menuPanel) return;
        if (show) {
            menuOverlay.classList.remove('invisible');
            setTimeout(() => {
                menuBackdrop?.classList.add('opacity-100');
                menuPanel.classList.remove('translate-x-full');
            }, 10);
            document.body.style.overflow = 'hidden';
        } else {
            menuBackdrop?.classList.remove('opacity-100');
            menuPanel.classList.add('translate-x-full');
            setTimeout(() => {
                menuOverlay.classList.add('invisible');
                const modalDinamico = document.getElementById('dynamic-modal-container');
                if (modalDinamico && modalDinamico.classList.contains('hidden')) {
                    document.body.style.overflow = 'auto';
                }
            }, 500);
        }
    };

    if (menuBtn) menuBtn.addEventListener('click', () => toggleMenu(true));
    if (closeMenuBtn) closeMenuBtn.addEventListener('click', () => toggleMenu(false));
    if (menuBackdrop) menuBackdrop.addEventListener('click', () => toggleMenu(false));

    document.addEventListener('keydown', (e) => {
        if (e.key === 'Escape') {
            closeDynamicModal();
            if (menuOverlay && !menuOverlay.classList.contains('invisible')) toggleMenu(false);
        }
    });

    const dynamicContainer = document.getElementById('dynamic-modal-container');
    if (dynamicContainer) {
        dynamicContainer.addEventListener('click', (e) => {
            if (e.target === dynamicContainer) closeDynamicModal();
        });
    }
});