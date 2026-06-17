// public/custom.js

window.addEventListener("message", (event) => {
  const data = event.data;
  //console.log(data);
  if(data?.type == "update-placeholder" && data.payload?.placeholder) {
    document.getElementById('chat-input').placeholder = data.payload.placeholder;
  }
  if(data?.type == "toggle-upload-files" && data.payload?.display) {
    ['dragover', 'drop'].forEach(t => {
      window.addEventListener(t, e => {
        e.preventDefault();
         e.stopPropagation();
          e.dataTransfer.dropEffect = 'none';
        },
        true
      );
    });
    const observer = new MutationObserver((mutations, obs) => {
      const el = document.getElementById('upload-button');
      if (el) {
        el.remove();
        obs.disconnect();   // stop watching – we’re done
      }
    });
    observer.observe(document.body, { childList: true, subtree: true });
  }
});

document.addEventListener('DOMContentLoaded', function() {
  const shareButton = document.getElementById('share-thread');
  if (shareButton) {
    // Remove the loading animation div
    const placeholder = shareButton.querySelector('.animate-pulse');
    if (placeholder) {
      placeholder.remove();
    }
    
    // Create and insert the text node before the SVG
    const textNode = document.createTextNode('Share');
    const textWrapper = document.createElement('span');
    textWrapper.appendChild(textNode);
    shareButton.insertBefore(textWrapper, shareButton.firstChild);
  }
  
  // Create the beta notification banner
  const banner = document.createElement('div');
  banner.id = 'beta-notification-banner';
  banner.innerHTML = '<div class="beta-notification-content"><span class="beta-notification-text">Scout Beta Launch: Please use the in-app <svg xmlns="http://www.w3.org/2000/svg" width="18" height="18" viewBox="0 0 24 24" fill="none" style="display: inline-block; vertical-align: middle;" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" class="lucide lucide-thumbs-up h-3 w-3" aria-hidden="true"><path d="M7 10v12"></path><path d="M15 5.88 14 10h5.83a2 2 0 0 1 1.92 2.56l-2.33 8A2 2 0 0 1 17.5 22H4a2 2 0 0 1-2-2v-8a2 2 0 0 1 2-2h2.76a2 2 0 0 0 1.79-1.11L12 2a3.13 3.13 0 0 1 3 3.88Z"></path></svg> / <svg xmlns="http://www.w3.org/2000/svg" width="18" height="18" viewBox="0 0 24 24" style="display: inline-block; vertical-align: middle;" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" class="lucide lucide-thumbs-down h-3 w-3" aria-hidden="true"><path d="M17 14V2"></path><path d="M9 18.12 10 14H4.17a2 2 0 0 1-1.92-2.56l2.33-8A2 2 0 0 1 6.5 2H20a2 2 0 0 1 2 2v8a2 2 0 0 1-2 2h-2.76a2 2 0 0 0-1.79 1.11L12 22a3.13 3.13 0 0 1-3-3.88Z"></path></svg> during your chat to provide feedback or send a message to the developers!</span> <button class="beta-notification-close">×</button></div>';
  
  // Insert banner at the beginning of body
  document.body.insertBefore(banner, document.body.firstChild);
  
  // Add a class to the body to indicate the banner is active
  document.body.classList.add('banner-is-visible');
  
  // Add event listener for close button
  const closeButton = banner.querySelector('.beta-notification-close');
  closeButton.addEventListener('click', function() {
    fadeOutBanner();
    // Store in session storage to keep it closed during this session
    sessionStorage.setItem('betaBannerClosed', 'true');
  });
  
  // Check if banner was previously closed
  if (sessionStorage.getItem('betaBannerClosed') === 'true') {
    banner.style.display = 'none';
    document.body.classList.remove('banner-is-visible');
  } else {
    // Auto-dismiss the banner after x seconds
    setTimeout(fadeOutBanner, 1);
  }
  
  // Function to fade out the banner
  function fadeOutBanner() {
    const banner = document.getElementById('beta-notification-banner');
    if (banner) {
      banner.style.transition = 'opacity 0.5s ease';
      banner.style.opacity = '0';
      setTimeout(() => {
        banner.style.display = 'none';
        // Remove the class from body when banner is hidden
        document.body.classList.remove('banner-is-visible');
      }, 500);
    }
  }
  
  // Add shimmer effect to specific links in message content
  function addShimmerToSpecialLinks() {
    // Target only links within message-content divs
    const messageContents = document.querySelectorAll('.message-content');
    
    messageContents.forEach(container => {
      // Find all links within this container
      const links = container.querySelectorAll('a.element-link');
      
      links.forEach(link => {
        const linkText = link.textContent.trim();
        // Only apply to specific link texts
        if(['Goals', 'Feedback', 'Awards', 'Self Assessment'].includes(linkText)) {
          // Add the special class
          link.classList.add('shimmer-link');
        }
      });
    });
  }
  
  // Run initially
  addShimmerToSpecialLinks();
  
  // Set up a mutation observer to check for dynamically added content
  const observer = new MutationObserver(function(mutations) {
    mutations.forEach(function(mutation) {
      if (mutation.addedNodes.length) {
        addShimmerToSpecialLinks();
      }
    });
  });
  
  // Start observing the document body for changes
  observer.observe(document.body, { childList: true, subtree: true });
});
