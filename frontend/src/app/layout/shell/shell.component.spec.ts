import { TestBed } from '@angular/core/testing';
import { provideRouter } from '@angular/router';
import { ShellComponent } from './shell.component';
import { AuthService } from '../../services/auth.service';

describe('ShellComponent - Versao Release Candidate e Layout', () => {
  let auth: AuthService;

  beforeEach(async () => {
    await TestBed.configureTestingModule({
      imports: [ShellComponent],
      providers: [AuthService, provideRouter([])],
    }).compileComponents();
    auth = TestBed.inject(AuthService);
  });

  it('deve exibir discretamente a tag de versao v1.0.0-rc.1 no rodape do sistema autenticado', () => {
    auth.setRole('admin');
    const fixture = TestBed.createComponent(ShellComponent);
    fixture.detectChanges();

    const el: HTMLElement = fixture.nativeElement;
    const footer = el.querySelector('.shell-footer');
    const versionTag = el.querySelector('[data-testid="app-version"]');

    expect(fixture.componentInstance.appVersion).toBe('v1.0.0-rc.1');
    expect(footer).not.toBeNull();
    expect(versionTag).not.toBeNull();
    expect(versionTag?.textContent?.trim()).toBe('v1.0.0-rc.1');
  });

  it('nao deve renderizar emojis no cabecalho ou rodape do shell', () => {
    auth.setRole('coordenador');
    const fixture = TestBed.createComponent(ShellComponent);
    fixture.detectChanges();

    const texto = (fixture.nativeElement as HTMLElement).textContent ?? '';
    expect(/[\u{1F300}-\u{1FAFF}]/u.test(texto)).toBeFalse();
  });
});
