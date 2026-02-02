import { describe, it, expect, vi, beforeEach } from 'vitest';
import { render, screen, waitFor } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import PasswordChange from './PasswordChange';

global.fetch = vi.fn();

describe('PasswordChange Component', () => {
  beforeEach(() => {
    fetch.mockClear();
  });

  it('renders password change form with required fields', () => {
    render(<PasswordChange />);

    expect(screen.getByLabelText(/current password/i)).toBeInTheDocument();
    expect(screen.getByLabelText(/new password/i)).toBeInTheDocument();
    expect(screen.getByRole('button', { name: /change password/i })).toBeInTheDocument();
  });

  it('renders the heading', () => {
    render(<PasswordChange />);

    expect(screen.getByRole('heading', { name: /change password/i })).toBeInTheDocument();
  });

  it('allows user to type passwords', async () => {
    const user = userEvent.setup();
    render(<PasswordChange />);

    const currentPasswordInput = screen.getByLabelText(/current password/i);
    const newPasswordInput = screen.getByLabelText(/new password/i);

    await user.type(currentPasswordInput, 'oldpass123');
    await user.type(newPasswordInput, 'newpass456');

    expect(currentPasswordInput).toHaveValue('oldpass123');
    expect(newPasswordInput).toHaveValue('newpass456');
  });

  it('shows success message when password change succeeds', async () => {
    const user = userEvent.setup();
    fetch.mockResolvedValue({
      ok: true,
      json: async () => ({ message: 'Password changed successfully' }),
    });

    render(<PasswordChange />);

    await user.type(screen.getByLabelText(/current password/i), 'oldpass123');
    await user.type(screen.getByLabelText(/new password/i), 'newpass456');
    await user.click(screen.getByRole('button', { name: /change password/i }));

    await waitFor(() => {
      expect(screen.getByText(/password changed successfully/i)).toBeInTheDocument();
    });
  });

  it('shows error message when password change fails', async () => {
    const user = userEvent.setup();
    fetch.mockResolvedValue({
      ok: false,
      json: async () => ({ detail: 'Current password is incorrect' }),
    });

    render(<PasswordChange />);

    await user.type(screen.getByLabelText(/current password/i), 'wrongpass');
    await user.type(screen.getByLabelText(/new password/i), 'newpass456');
    await user.click(screen.getByRole('button', { name: /change password/i }));

    await waitFor(() => {
      expect(screen.getByText(/current password is incorrect/i)).toBeInTheDocument();
    });
  });

  it('clears form fields after successful password change', async () => {
    const user = userEvent.setup();
    fetch.mockResolvedValue({
      ok: true,
      json: async () => ({ message: 'Password changed successfully' }),
    });

    render(<PasswordChange />);

    const currentPasswordInput = screen.getByLabelText(/current password/i);
    const newPasswordInput = screen.getByLabelText(/new password/i);

    await user.type(currentPasswordInput, 'oldpass123');
    await user.type(newPasswordInput, 'newpass456');
    await user.click(screen.getByRole('button', { name: /change password/i }));

    await waitFor(() => {
      expect(currentPasswordInput).toHaveValue('');
      expect(newPasswordInput).toHaveValue('');
    });
  });

  it('shows loading state during password change', async () => {
    const user = userEvent.setup();
    let resolveFetch;
    fetch.mockImplementation(() => new Promise((resolve) => {
      resolveFetch = resolve;
    }));

    render(<PasswordChange />);

    await user.type(screen.getByLabelText(/current password/i), 'oldpass123');
    await user.type(screen.getByLabelText(/new password/i), 'newpass456');
    await user.click(screen.getByRole('button', { name: /change password/i }));

    expect(screen.getByRole('button', { name: /changing/i })).toBeInTheDocument();
    expect(screen.getByRole('button')).toBeDisabled();

    resolveFetch({ ok: true, json: async () => ({}) });
  });

  it('enforces minimum password length of 8 characters', () => {
    render(<PasswordChange />);

    const newPasswordInput = screen.getByLabelText(/new password/i);
    expect(newPasswordInput).toHaveAttribute('minLength', '8');
  });

  it('requires both password fields', () => {
    render(<PasswordChange />);

    const currentPasswordInput = screen.getByLabelText(/current password/i);
    const newPasswordInput = screen.getByLabelText(/new password/i);

    expect(currentPasswordInput).toBeRequired();
    expect(newPasswordInput).toBeRequired();
  });
});
