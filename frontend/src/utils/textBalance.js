/**
 * Text balance utility to prevent orphaned words (less than 3 words per line)
 * Works with CSS text-wrap: balance and orphans/widows properties
 */

/**
 * Groups words into chunks of at least minWordsPerLine to ensure no line has fewer words
 * Uses non-breaking spaces within chunks, regular spaces between chunks
 */
function groupWordsIntoChunks(words, minWordsPerLine = 3) {
  if (words.length <= minWordsPerLine) {
    // If total words <= minWordsPerLine, keep them all together
    return [words];
  }

  const chunks = [];
  let i = 0;
  
  while (i < words.length) {
    const remainingWords = words.length - i;
    
    // If remaining words are exactly minWordsPerLine or less, add them all to current chunk
    if (remainingWords <= minWordsPerLine) {
      chunks.push(words.slice(i));
      break;
    }
    
    // Take minWordsPerLine words for this chunk
    chunks.push(words.slice(i, i + minWordsPerLine));
    i += minWordsPerLine;
    
    // If after taking this chunk, remaining words are less than minWordsPerLine,
    // merge them with the last chunk to avoid orphans
    const stillRemaining = words.length - i;
    if (stillRemaining > 0 && stillRemaining < minWordsPerLine && chunks.length > 0) {
      chunks[chunks.length - 1].push(...words.slice(i));
      break;
    }
  }
  
  return chunks;
}

/**
 * Adjusts text content to prevent lines with less than 3 words
 * Groups words into chunks of at least 3 words and uses non-breaking spaces within chunks
 */
export function preventOrphanedWords(element, minWordsPerLine = 3) {
  if (!element) return;

  // Skip code/monospace elements
  const computedStyle = window.getComputedStyle(element);
  if (computedStyle.fontFamily.includes('mono') || 
      computedStyle.fontFamily.includes('Mono') ||
      element.tagName === 'CODE' || 
      element.tagName === 'PRE') {
    return;
  }

  const walker = document.createTreeWalker(
    element,
    NodeFilter.SHOW_TEXT,
    {
      acceptNode: (node) => {
        // Skip text nodes inside code/pre elements
        let parent = node.parentElement;
        while (parent && parent !== element) {
          if (parent.tagName === 'CODE' || parent.tagName === 'PRE') {
            return NodeFilter.FILTER_REJECT;
          }
          parent = parent.parentElement;
        }
        return NodeFilter.FILTER_ACCEPT;
      }
    }
  );

  const textNodes = [];
  let node;
  while ((node = walker.nextNode())) {
    const text = node.textContent.trim();
    if (text.length > 0) {
      textNodes.push(node);
    }
  }

  textNodes.forEach((textNode) => {
    const originalText = textNode.textContent;
    const words = originalText.trim().split(/\s+/).filter(w => w.length > 0);
    
    // Only process if there are enough words
    if (words.length >= minWordsPerLine) {
      // Group words into chunks of at least minWordsPerLine
      const chunks = groupWordsIntoChunks(words, minWordsPerLine);
      
      // Join words within chunks with non-breaking spaces
      // Join chunks with regular spaces
      const processedChunks = chunks.map(chunk => chunk.join('\u00A0'));
      const newText = processedChunks.join(' ');
      
      // Preserve leading/trailing whitespace from original
      const leadingWhitespace = originalText.match(/^\s*/)?.[0] || '';
      const trailingWhitespace = originalText.match(/\s*$/)?.[0] || '';
      
      textNode.textContent = leadingWhitespace + newText + trailingWhitespace;
    }
  });
}

/**
 * Apply text balance to all text elements on the page
 */
export function applyTextBalance(minWordsPerLine = 3) {
  // Select key text containers (exclude code/monospace elements)
  // Focus on headings and important text blocks
  const selectors = [
    'h1', 'h2', 'h3', 'h4', 'h5', 'h6',
    'p', 'li',
    '.hero-title', '.hero-subtitle', '.section-title', '.section-text',
    '.subsection-title', '.hero-subtext',
    '.feature-card', '.enterprise-card', '.integration-card',
    '.detector-chat .section-title', '.detector-chat .section-text',
    '.contact-info', '.verdict-explainer', '.detail-text',
    '.form-info-text', '.demo-notice', '.demo-disclaimer-box',
    '.upload-instructions p', '.footer-legal p', '.privacy-text span'
  ].join(', ');

  const elements = document.querySelectorAll(selectors);
  elements.forEach((element) => {
    // Only apply to elements that are visible and have at least minWordsPerLine words
    const wordCount = element.textContent.trim().split(/\s+/).filter(w => w.length > 0).length;
    if (element.offsetHeight > 0 && wordCount >= minWordsPerLine) {
      preventOrphanedWords(element, minWordsPerLine);
    }
  });
}

// Module-level state for singleton pattern
let isInitialized = false;
let debounceTimer = null;
let observer = null;

/**
 * Initialize text balance on page load and after dynamic content changes
 */
export function initTextBalance() {
  // Prevent multiple initializations
  if (isInitialized) {
    return;
  }
  isInitialized = true;

  // Apply on initial load
  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', () => {
      setTimeout(applyTextBalance, 100); // Small delay for fonts to load
    });
  } else {
    setTimeout(applyTextBalance, 100);
  }

  // Debounce function to prevent excessive calls
  const debouncedApplyTextBalance = () => {
    if (debounceTimer) {
      clearTimeout(debounceTimer);
    }
    debounceTimer = setTimeout(applyTextBalance, 150);
  };

  // Re-apply when content changes (for React components)
  observer = new MutationObserver(debouncedApplyTextBalance);

  observer.observe(document.body, {
    childList: true,
    subtree: true,
    characterData: true
  });
}

