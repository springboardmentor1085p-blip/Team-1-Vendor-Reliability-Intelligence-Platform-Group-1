import { Component, OnInit } from '@angular/core';
import { VendorService } from '../../services/vendor.service';
import { AuthService } from '../../services/auth.service';

@Component({
  selector: 'app-reliability',
  templateUrl: './reliability.component.html',
  styleUrls: ['./reliability.component.css']
})
export class ReliabilityComponent implements OnInit {
  rankedVendors: any[] = [];
  loading = false;

  constructor(
    private vendorService: VendorService,
    public authService: AuthService
  ) {}

  ngOnInit(): void {
    this.loadRanking();
  }

  loadRanking(): void {
    this.loading = true;
    this.vendorService.getVendorRanking().subscribe({
      next: (data) => {
        this.rankedVendors = data;
        this.loading = false;
      },
      error: (err) => {
        console.error('Error loading vendor rankings', err);
        this.loading = false;
      }
    });
  }
}
