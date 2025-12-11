import '@testing-library/jest-dom';

// Mock scrollIntoView which doesn't exist in jsdom
window.HTMLElement.prototype.scrollIntoView = function () { };
