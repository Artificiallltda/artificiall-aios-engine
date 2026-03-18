/* =============================================
   ARTIFICIALL — Main JavaScript
   ============================================= */


// ─── Utilitários de Performance ──────────────────
// Throttle: garante execução no máximo uma vez a cada intervalo
function throttle(func, limit) {
  let inThrottle;
  return function(...args) {
    const context = this;
    if (!inThrottle) {
      func.apply(context, args);
      inThrottle = true;
      setTimeout(() => inThrottle = false, limit);
    }
  };
}

// Debounce: executa apenas após um período de inatividade
function debounce(func, wait) {
  let timeout;
  return function(...args) {
    const context = this;
    clearTimeout(timeout);
    timeout = setTimeout(() => func.apply(context, args), wait);
  };
}

// ─── Acessibilidade: Movimento Reduzido ────────
// Detectar preferência por movimento reduzido (sistema operacional)
const prefersReducedMotion = window.matchMedia('(prefers-reduced-motion: reduce)').matches;

// Função utilitária para verificar dinâmica / runtime
function shouldAnimate() {
  return !window.matchMedia('(prefers-reduced-motion: reduce)').matches;
}

// ─── Navbar scroll effect ──────────────────────
const navbar = document.getElementById('navbar');

const handleScroll = throttle(() => {
  if (window.scrollY > 50) {
    navbar.classList.add('scrolled');
  } else {
    navbar.classList.remove('scrolled');
  }
}, 100); // Executa no máximo a cada 100ms

window.addEventListener('scroll', handleScroll, { passive: true });

// ─── Mobile Menu ───────────────────────────────
const hamburger = document.getElementById('hamburger');
const mobileMenu = document.getElementById('mobileMenu');
const mobileClose = document.getElementById('mobileClose');

// ─── Acessibilidade: Focus Trap ────────────────
// Captura o foco dentro do `container` enquanto o menu está aberto.
// Isso garante que usuários de teclado/leitores de tela não "escapem"
// para o conteúdo de fundo — WCAG 2.1 critério 2.1.2.
function trapFocus(container) {
  const focusableSelectors = [
    'button:not([disabled])',
    'a[href]:not([disabled])',
    'input:not([disabled])',
    'select:not([disabled])',
    'textarea:not([disabled])',
    '[tabindex]:not([tabindex="-1"])'
  ].join(', ');

  const focusableElements = container.querySelectorAll(focusableSelectors);
  if (focusableElements.length === 0) return;

  const firstFocusable = focusableElements[0];
  const lastFocusable  = focusableElements[focusableElements.length - 1];

  // Remove listener anterior para evitar duplicação em aberturas consecutivas
  container.removeEventListener('keydown', container._trapHandler);

  function handleTrapKeydown(e) {
    if (e.key !== 'Tab') return;

    if (e.shiftKey) {
      // Shift+Tab no primeiro elemento → salta para o último
      if (document.activeElement === firstFocusable) {
        e.preventDefault();
        lastFocusable.focus();
      }
    } else {
      // Tab no último elemento → salta para o primeiro
      if (document.activeElement === lastFocusable) {
        e.preventDefault();
        firstFocusable.focus();
      }
    }
  }

  // Armazena referência no elemento para poder remover depois
  container._trapHandler = handleTrapKeydown;
  container.addEventListener('keydown', handleTrapKeydown);

  // Foca no primeiro elemento ao abrir o menu
  firstFocusable.focus();
}

function openMobileMenu() {
  mobileMenu.classList.add('open');
  document.body.style.overflow = 'hidden';
  // Ativa o focus trap e move o foco para dentro do menu
  trapFocus(mobileMenu);
}

hamburger.addEventListener('click', openMobileMenu);

mobileClose.addEventListener('click', closeMobile);

// Adicionar listener para fechar com ESC
mobileMenu.addEventListener('keydown', (e) => {
  if (e.key === 'Escape') {
    closeMobile();
  }
});

function closeMobile() {
  mobileMenu.classList.remove('open');
  document.body.style.overflow = '';
  // Libera o trap e devolve o foco ao botão que abriu o menu
  mobileMenu.removeEventListener('keydown', mobileMenu._trapHandler);
  hamburger.focus();
}

// ─── Hero Particle Canvas ─────────────────────
(function initParticles() {
  if (!shouldAnimate()) return; // WCAG: Não inicia partículas se usuário prefere redução de movimento

  const canvas = document.getElementById('hero-canvas');
  if (!canvas) return;
  const ctx = canvas.getContext('2d');

  function resize() {
    canvas.width = canvas.offsetWidth;
    canvas.height = canvas.offsetHeight;
  }

  resize();
  // Debounce de 150ms: evita recálculos excessivos durante redimensionamento da janela
  const debouncedResize = debounce(() => {
    canvas.width = canvas.offsetWidth;
    canvas.height = canvas.offsetHeight;
  }, 150);
  window.addEventListener('resize', debouncedResize, { passive: true });

  const COLORS = ['rgba(0,163,255,', 'rgba(124,58,237,', 'rgba(245,158,11,'];
  const particles = [];

  class Particle {
    constructor() { this.reset(); }
    reset() {
      this.x = Math.random() * canvas.width;
      this.y = Math.random() * canvas.height;
      this.size = Math.random() * 1.8 + 0.4;
      this.speedX = (Math.random() - 0.5) * 0.4;
      this.speedY = (Math.random() - 0.5) * 0.4;
      this.color = COLORS[Math.floor(Math.random() * COLORS.length)];
      this.opacity = Math.random() * 0.5 + 0.1;
      this.life = 0;
      this.maxLife = Math.random() * 300 + 200;
    }
    update() {
      this.x += this.speedX;
      this.y += this.speedY;
      this.life++;
      if (this.life > this.maxLife) this.reset();
      if (this.x < 0 || this.x > canvas.width || this.y < 0 || this.y > canvas.height) this.reset();
    }
    draw() {
      const fade = this.life / this.maxLife;
      const alpha = this.opacity * (1 - fade * 0.5);
      ctx.beginPath();
      ctx.arc(this.x, this.y, this.size, 0, Math.PI * 2);
      ctx.fillStyle = this.color + alpha + ')';
      ctx.fill();
    }
  }

  // Create particles and lines
  for (let i = 0; i < 120; i++) {
    particles.push(new Particle());
  }

  function drawConnections() {
    const maxDist = 100;
    for (let i = 0; i < particles.length; i++) {
      for (let j = i + 1; j < particles.length; j++) {
        const dx = particles[i].x - particles[j].x;
        const dy = particles[i].y - particles[j].y;
        const dist = Math.sqrt(dx * dx + dy * dy);
        if (dist < maxDist) {
          const alpha = (1 - dist / maxDist) * 0.06;
          ctx.beginPath();
          ctx.moveTo(particles[i].x, particles[i].y);
          ctx.lineTo(particles[j].x, particles[j].y);
          ctx.strokeStyle = `rgba(0,163,255,${alpha})`;
          ctx.lineWidth = 0.5;
          ctx.stroke();
        }
      }
    }
  }

  // Controle de FPS: limita a animação a 30 quadros/s para economizar CPU e bateria
  let animationFrame;
  let lastFrameTime = 0;
  const FPS = 30;
  const frameInterval = 1000 / FPS;

  function animate(currentTime) {
    animationFrame = requestAnimationFrame(animate);

    // Pula o frame se ainda não passou tempo suficiente desde o último
    if (currentTime - lastFrameTime < frameInterval) return;
    lastFrameTime = currentTime;

    ctx.clearRect(0, 0, canvas.width, canvas.height);
    particles.forEach(p => { p.update(); p.draw(); });
    drawConnections();
  }

  animate();

  // Pausa o canvas quando a aba está oculta e retoma ao voltar
  document.addEventListener('visibilitychange', () => {
    if (document.hidden) {
      cancelAnimationFrame(animationFrame);
    } else {
      animationFrame = requestAnimationFrame(animate);
    }
  });
})();

// ─── Scroll Reveal (Intersection Observer) ────
(function initReveal() {
  const elements = document.querySelectorAll('.reveal');

  const observer = new IntersectionObserver((entries) => {
    entries.forEach((entry, i) => {
      if (entry.isIntersecting) {
        setTimeout(() => {
          entry.target.classList.add('visible');
        }, i * 60);
        observer.unobserve(entry.target);
      }
    });
  }, { threshold: 0.1, rootMargin: '0px 0px -40px 0px' });

  elements.forEach(el => observer.observe(el));
})();

// ─── Smooth Scroll ─────────────────────────────
document.querySelectorAll('a[href^="#"]').forEach(anchor => {
  anchor.addEventListener('click', function (e) {
    const target = document.querySelector(this.getAttribute('href'));
    if (target) {
      e.preventDefault();
      const navH = 72;
      const top = target.getBoundingClientRect().top + window.scrollY - navH;
      window.scrollTo({ top, behavior: 'smooth' });
    }
  });
});

// ─── Active Nav Link ──────────────────────────
(function initActiveNav() {
  const sections = document.querySelectorAll('section[id]');
  const navLinks = document.querySelectorAll('.nav-links .nav-link');

  const observer = new IntersectionObserver((entries) => {
    entries.forEach(entry => {
      if (entry.isIntersecting) {
        navLinks.forEach(link => {
          link.classList.remove('active');
          if (link.getAttribute('href') === '#' + entry.target.id) {
            link.classList.add('active');
          }
        });
      }
    });
  }, { threshold: 0.4 });

  sections.forEach(s => observer.observe(s));
})();

// ─── Lazy Loading de Imagens ──────────────────
function initLazyLoading() {
  const images = document.querySelectorAll('img.lazyload');
  
  if (!images.length) return;
  
  const imageObserver = new IntersectionObserver((entries, observer) => {
    entries.forEach(entry => {
      if (entry.isIntersecting) {
        const img = entry.target;
        img.src = img.dataset.src;
        img.classList.add('loaded');
        observer.unobserve(img);
      }
    });
  }, {
    rootMargin: '50px 0px', // Carrega 50px antes de entrar na viewport
    threshold: 0.01
  });
  
  images.forEach(img => imageObserver.observe(img));
}

// Chamar a função no carregamento da página
document.addEventListener('DOMContentLoaded', initLazyLoading);

// ─── Number Counter Animation ─────────────────
(function initCounters() {
  const stats = document.querySelectorAll('.stat-number');

  const observer = new IntersectionObserver((entries) => {
    entries.forEach(entry => {
      if (entry.isIntersecting) {
        const el = entry.target;
        const text = el.textContent;
        const isNumber = /^\d+/.test(text);

        if (isNumber) {
          const target = parseInt(text);
          let current = 0;
          const increment = target / 50;
          const suffix = text.replace(/[\d]/g, '');

          const timer = setInterval(() => {
            current += increment;
            if (current >= target) {
              current = target;
              clearInterval(timer);
            }
            el.textContent = Math.round(current) + suffix;
          }, 30);
        }
        observer.unobserve(el);
      }
    });
  }, { threshold: 0.5 });

  stats.forEach(s => observer.observe(s));
})();

// product card scroll-into-section btn
document.querySelectorAll('.product-card').forEach(card => {
  card.addEventListener('click', () => {
    const link = card.querySelector('a');
    if (link) link.click();
  });
});

// ─── Typing effect on hero subtitle ──────────
(function initTyping() {
  if (!shouldAnimate()) {
    const el = document.querySelector('.hero-sub');
    if (el) el.textContent = 'Transforme sua empresa com a IA mais completa do mercado.';
    return;
  }
  
  const taglines = [
    'Transforme sua empresa com a IA mais completa do mercado.',
    'Uma plataforma, múltiplos modelos, resultados extraordinários.',
    'Agentes autônomos que trabalham enquanto você descansa.'
  ];

  const el = document.querySelector('.hero-sub');
  if (!el) return;

  let currentPhrase = 0;
  let currentChar = 0;
  let isDeleting = false;
  let lastUpdate = 0;
  const typingSpeed = 40;
  const deletingSpeed = 20;
  const pauseDuration = 2000;

  function typeAnimation(currentTime) {
    if (currentTime - lastUpdate < (isDeleting ? deletingSpeed : typingSpeed)) {
      requestAnimationFrame(typeAnimation);
      return;
    }
    lastUpdate = currentTime;

    const phrase = taglines[currentPhrase];
    
    if (!isDeleting) {
      el.textContent = phrase.substring(0, currentChar + 1);
      currentChar++;
      
      if (currentChar === phrase.length) {
        isDeleting = true;
        setTimeout(() => {
          requestAnimationFrame(typeAnimation);
        }, pauseDuration);
        return;
      }
    } else {
      el.textContent = phrase.substring(0, currentChar - 1);
      currentChar--;
      
      if (currentChar === 0) {
        isDeleting = false;
        currentPhrase = (currentPhrase + 1) % taglines.length;
      }
    }
    
    requestAnimationFrame(typeAnimation);
  }

  // Iniciar a animação
  requestAnimationFrame(typeAnimation);
})();

console.log('%c ARTIFICIALL 🔺', 'color:#00a3ff; font-size:20px; font-weight:900;');
console.log('%c Ecossistema Premium de IA', 'color:#94a3b8; font-size:14px;');

// ─── Service Worker (PWA / Offline) ────────────
if ('serviceWorker' in navigator) {
  window.addEventListener('load', () => {
    navigator.serviceWorker.register('/sw.js')
      .then(registration => {
        console.log('ServiceWorker registrado: ', registration.scope);
      })
      .catch(error => {
        console.log('Falha no ServiceWorker: ', error);
      });
  });
}
