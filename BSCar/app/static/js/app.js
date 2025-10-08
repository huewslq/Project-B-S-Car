console.log('BSCar app loaded');

document.addEventListener('DOMContentLoaded', () => {
  const chips = document.querySelectorAll('.chip:not([href])');
  if (!chips.length) return;
  const hasActive = Array.from(chips).some((c) => c.classList.contains('is-active'));
  if (!hasActive) {
    chips[0].classList.add('is-active');
  }
  chips.forEach((chip) => {
    chip.addEventListener('click', () => {
      chips.forEach((c) => c.classList.remove('is-active'));
      chip.classList.add('is-active');
    });
  });

  const fileInput = document.getElementById('images');
  const previewContainer = document.getElementById('image-preview');
  
  if (fileInput && previewContainer) {
    fileInput.addEventListener('change', handleFileSelect);
  }
});

function handleFileSelect(event) {
  const files = event.target.files;
  const previewContainer = document.getElementById('image-preview');
  
  previewContainer.innerHTML = '';
  
  Array.from(files).forEach((file, index) => {
    if (file.type.startsWith('image/')) {
      if (file.size > 5 * 1024 * 1024) {
        alert(`Файл ${file.name} слишком большой (максимум 5MB)`);
        return;
      }
      
      const reader = new FileReader();
      reader.onload = function(e) {
        const previewItem = document.createElement('div');
        previewItem.className = 'preview-item';
        previewItem.innerHTML = `
          <img src="${e.target.result}" alt="Preview">
          <button type="button" class="remove-btn" onclick="removePreview(${index})">×</button>
        `;
        previewContainer.appendChild(previewItem);
      };
      reader.readAsDataURL(file);
    } else {
      alert(`Файл ${file.name} не является изображением`);
    }
  });
}

function removePreview(index) {
  const fileInput = document.getElementById('images');
  const previewContainer = document.getElementById('image-preview');
  
  const previewItems = previewContainer.querySelectorAll('.preview-item');
  if (previewItems[index]) {
    previewItems[index].remove();
  }
  
  const dt = new DataTransfer();
  const files = Array.from(fileInput.files);
  files.forEach((file, i) => {
    if (i !== index) {
      dt.items.add(file);
    }
  });
  fileInput.files = dt.files;
}

function changeMainImage(thumbnail) {
  const mainImage = document.getElementById('main-image');
  if (mainImage && thumbnail) {
    mainImage.src = thumbnail.src;
    
    document.querySelectorAll('.thumbnail').forEach(thumb => {
      thumb.classList.remove('active');
    });
    thumbnail.classList.add('active');
  }
}

document.addEventListener('DOMContentLoaded', () => {
  const chatMessages = document.getElementById('chat-messages');
  if (chatMessages) {
    chatMessages.scrollTop = chatMessages.scrollHeight;
  }
  
  const messageInput = document.querySelector('.message-input');
  if (messageInput) {
    messageInput.focus();
  }
  
  const searchInput = document.querySelector('input[name="search"]');
  if (searchInput) {
    searchInput.addEventListener('keypress', function(e) {
      if (e.key === 'Enter') {
        this.form.submit();
      }
    });
    
    searchInput.addEventListener('keydown', function(e) {
      if (e.key === 'Escape') {
        this.value = '';
        this.form.submit();
      }
    });
  }
});

function showAddAdminForm() {
    document.getElementById('add-admin-form').style.display = 'block';
    document.getElementById('block-user-form').style.display = 'none';
    document.getElementById('delete-listing-form').style.display = 'none';
}

function hideAddAdminForm() {
    document.getElementById('add-admin-form').style.display = 'none';
}

function showBlockUserForm() {
    document.getElementById('block-user-form').style.display = 'block';
    document.getElementById('add-admin-form').style.display = 'none';
    document.getElementById('delete-listing-form').style.display = 'none';
}

function hideBlockUserForm() {
    document.getElementById('block-user-form').style.display = 'none';
}

function showDeleteListingForm() {
    document.getElementById('delete-listing-form').style.display = 'block';
    document.getElementById('add-admin-form').style.display = 'none';
    document.getElementById('block-user-form').style.display = 'none';
}

function hideDeleteListingForm() {
    document.getElementById('delete-listing-form').style.display = 'none';
}
