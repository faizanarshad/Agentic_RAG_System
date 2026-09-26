'use client';

import { useState } from 'react';
import { CircleAlert, CircleCheck, Loader2, Send } from 'lucide-react';
import { API_BASE } from '@/lib/api';

const TOPICS = [
  { value: 'engineering', label: 'Engineering drawing review' },
  { value: 'legal', label: 'Legal document synthesis' },
  { value: 'medical', label: 'Clinical document Q&A' },
  { value: 'pilot', label: 'Pilot or evaluation' },
  { value: 'integration', label: 'Integration or API' },
  { value: 'other', label: 'Something else' },
];

const EMAIL_PATTERN = /^[^\s@]+@[^\s@]+\.[^\s@]{2,}$/;

function validate(values) {
  const errors = {};
  if (values.name.trim().length < 2) errors.name = 'Please enter your name.';
  if (!EMAIL_PATTERN.test(values.email.trim())) errors.email = 'Please enter a valid email address.';
  if (values.message.trim().length < 20) errors.message = 'Please tell us a little more (at least 20 characters).';
  if (!values.consent) errors.consent = 'Please agree so we can reply to you.';
  return errors;
}

export default function ContactForm() {
  const [values, setValues] = useState({ name: '', email: '', company: '', topic: 'engineering', message: '', consent: false, website: '' });
  const [errors, setErrors] = useState({});
  const [status, setStatus] = useState({ state: 'idle', message: '' });

  const update = (field) => (event) => {
    const value = event.target.type === 'checkbox' ? event.target.checked : event.target.value;
    setValues((current) => ({ ...current, [field]: value }));
    if (errors[field]) setErrors((current) => ({ ...current, [field]: undefined }));
  };

  const submit = async (event) => {
    event.preventDefault();
    const found = validate(values);
    setErrors(found);
    if (Object.keys(found).length) {
      document.getElementById(`contact-${Object.keys(found)[0]}`)?.focus();
      return;
    }
    setStatus({ state: 'sending', message: '' });
    try {
      const response = await fetch(`${API_BASE}/contact`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(values),
      });
      const data = await response.json().catch(() => ({}));
      if (!response.ok) throw new Error(typeof data.detail === 'string' ? data.detail : 'Your message could not be sent.');
      setStatus({ state: 'sent', message: 'Thank you. Your message has been received and we will reply by email.' });
      setValues({ name: '', email: '', company: '', topic: values.topic, message: '', consent: false, website: '' });
    } catch (error) {
      setStatus({ state: 'error', message: `${error.message} Please try again in a moment.` });
    }
  };

  const describedBy = (field) => (errors[field] ? `contact-${field}-error` : undefined);

  return (
    <form className="form" onSubmit={submit} noValidate aria-labelledby="contact-form-title">
      <h2 id="contact-form-title" className="h3">Send us a message</h2>

      <div className="form__row">
        <div className="field">
          <label htmlFor="contact-name">Name</label>
          <input id="contact-name" name="name" autoComplete="name" value={values.name} onChange={update('name')}
            aria-invalid={Boolean(errors.name)} aria-describedby={describedBy('name')} required />
          {errors.name && <p id="contact-name-error" className="field__error">{errors.name}</p>}
        </div>
        <div className="field">
          <label htmlFor="contact-email">Work email</label>
          <input id="contact-email" name="email" type="email" autoComplete="email" inputMode="email" value={values.email}
            onChange={update('email')} aria-invalid={Boolean(errors.email)} aria-describedby={describedBy('email')} required />
          {errors.email && <p id="contact-email-error" className="field__error">{errors.email}</p>}
        </div>
      </div>

      <div className="form__row">
        <div className="field">
          <label htmlFor="contact-company">Company <span>(optional)</span></label>
          <input id="contact-company" name="company" autoComplete="organization" value={values.company} onChange={update('company')} />
        </div>
        <div className="field">
          <label htmlFor="contact-topic">Topic</label>
          <select id="contact-topic" name="topic" value={values.topic} onChange={update('topic')}>
            {TOPICS.map((t) => <option key={t.value} value={t.value}>{t.label}</option>)}
          </select>
        </div>
      </div>

      <div className="field">
        <label htmlFor="contact-message">How can we help?</label>
        <textarea id="contact-message" name="message" value={values.message} onChange={update('message')} maxLength={5000}
          placeholder="For example: we release around 40 drawings a month and want to check title blocks, tolerances and revision tables before sign-off."
          aria-invalid={Boolean(errors.message)} aria-describedby={describedBy('message')} required />
        {errors.message && <p id="contact-message-error" className="field__error">{errors.message}</p>}
      </div>

      {/* Honeypot: hidden from people, often filled by bots */}
      <div className="honeypot" aria-hidden="true">
        <label htmlFor="contact-website">Website</label>
        <input id="contact-website" name="website" tabIndex={-1} autoComplete="off" value={values.website} onChange={update('website')} />
      </div>

      <div className="field">
        <label className="consent" htmlFor="contact-consent">
          <input id="contact-consent" type="checkbox" checked={values.consent} onChange={update('consent')}
            aria-invalid={Boolean(errors.consent)} aria-describedby={describedBy('consent')} />
          <span>I agree that AIDocumentAgent may store this message and contact me about my enquiry.</span>
        </label>
        {errors.consent && <p id="contact-consent-error" className="field__error">{errors.consent}</p>}
      </div>

      <div aria-live="polite">
        {status.state === 'sent' && (
          <p className="form-status form-status--success"><CircleCheck size={18} aria-hidden="true" />{status.message}</p>
        )}
        {status.state === 'error' && (
          <p className="form-status form-status--error"><CircleAlert size={18} aria-hidden="true" />{status.message}</p>
        )}
      </div>

      <div>
        <button className="btn btn--primary" type="submit" disabled={status.state === 'sending'}>
          {status.state === 'sending' ? <Loader2 size={17} aria-hidden="true" /> : <Send size={17} aria-hidden="true" />}
          {status.state === 'sending' ? 'Sending…' : 'Send message'}
        </button>
      </div>
    </form>
  );
}
